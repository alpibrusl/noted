"""Assemble Season 2 episode voice lines into a single MP3 per episode.

Simple concatenation with inter-line silences — no background tracks or SFX
(the scripts carry the mood). For each episode, reads script.json, collects
voices/{id}.mp3 files, and ffmpeg-concatenates them with configurable silence.

Usage:
    # All episodes:
    python3 assemble_season2.py

    # One series:
    python3 assemble_season2.py --series compliant

    # One episode:
    python3 assemble_season2.py --series null_pointer --episode 4
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEASON2 = HERE / "season2"
INTROS_DIR = SEASON2 / "intros"
SAMPLE_RATE = 44100

# Silence between lines, in seconds.
SILENCE_BETWEEN = 0.55       # default inter-line gap
SILENCE_PARAGRAPH = 1.1      # longer gap before narrator blocks that open new scenes
TAIL_PAD = 3.0               # silence appended at the end

# NOTED intro/outro frame timings.
INTRO_PRE   = 1.2   # silence before "NOTED."
INTRO_MID   = 0.9   # silence between "NOTED." and series title
INTRO_POST  = 1.6   # silence between series title and first line
OUTRO_PRE   = 1.8   # silence after last line before "NOTED."
OUTRO_POST  = 2.5   # silence after final "NOTED."

# Characters whose lines get the longer pre-silence gap.
NARRATOR_CHARS = {"NARRATOR", "LUMEN", "HERALD"}

SERIES_EPISODES: dict[str, list[str]] = {
    "compliant":     [f"compliant_ep{i}" for i in range(1, 7)],
    "eight_minutes": [f"eight_minutes_ep{i}" for i in range(1, 7)],
    "null_pointer":  [f"null_pointer_ep{i}" for i in range(1, 7)],
    "deprecated":    [f"deprecated_ep{i}" for i in range(1, 7)],
}


def run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(f"Command failed: {' '.join(cmd[:5])}...\n{result.stderr}\n")
        raise SystemExit(result.returncode)


def ffprobe_dur(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def silence_file(duration: float, tmpdir: Path, idx: int) -> Path:
    dest = tmpdir / f"sil_{idx:04d}.wav"
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-t", f"{duration:.3f}",
        "-i", f"anullsrc=r={SAMPLE_RATE}:cl=stereo",
        str(dest),
    ])
    return dest


def check_intros(series_key: str, ep_num: int) -> tuple[Path, Path, Path] | None:
    """Return (noted, title_line, noted) paths or None if any are missing."""
    noted = INTROS_DIR / "noted.mp3"
    title = INTROS_DIR / f"{series_key}_ep{ep_num}.mp3"
    if not noted.exists():
        print(f"  WARNING: {noted} missing — run generate_intros.py first", file=sys.stderr)
        return None
    if not title.exists():
        print(f"  WARNING: {title} missing — run generate_intros.py first", file=sys.stderr)
        return None
    return noted, title, noted


def assemble_episode(ep_dir: Path, series_key: str, ep_num: int) -> bool:
    script_path = ep_dir / "script.json"
    voices_dir = ep_dir / "voices"
    if not script_path.exists():
        print(f"  {ep_dir.name}: no script.json — skipped", file=sys.stderr)
        return False

    script = json.loads(script_path.read_text(encoding="utf-8"))

    # Check all voice files exist
    missing = [e["id"] for e in script if not (voices_dir / f"{e['id']}.mp3").exists()]
    if missing:
        print(f"  {ep_dir.name}: missing voice files {missing[:5]}{'...' if len(missing) > 5 else ''} — run generate_season2.py first", file=sys.stderr)
        return False

    intro_pieces = check_intros(series_key, ep_num)
    has_frame = intro_pieces is not None
    noted_path, title_path, _ = intro_pieces if has_frame else (None, None, None)

    output = ep_dir / f"episode_{ep_num:02d}.mp3"
    print(f"  {ep_dir.name}  ->  {output.name}{'  [NOTED frame]' if has_frame else '  [no frame]'}")

    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        parts: list[Path] = []
        sil_idx = 0

        def sil(dur: float) -> Path:
            nonlocal sil_idx
            p = silence_file(dur, tmpdir, sil_idx)
            sil_idx += 1
            return p

        # ── INTRO FRAME ──────────────────────────────────────────────
        if has_frame:
            parts.append(sil(INTRO_PRE))
            parts.append(noted_path)
            parts.append(sil(INTRO_MID))
            parts.append(title_path)
            parts.append(sil(INTRO_POST))

        # ── EPISODE CONTENT ──────────────────────────────────────────
        prev_char = None
        for i, entry in enumerate(script):
            char = entry["character"]
            voice_file = voices_dir / f"{entry['id']}.mp3"

            if i == 0:
                gap = 0.0 if has_frame else SILENCE_BETWEEN
            elif char in NARRATOR_CHARS and prev_char not in NARRATOR_CHARS:
                gap = SILENCE_PARAGRAPH
            elif prev_char in NARRATOR_CHARS and char not in NARRATOR_CHARS:
                gap = SILENCE_PARAGRAPH
            else:
                gap = SILENCE_BETWEEN

            if gap > 0:
                parts.append(sil(gap))
            parts.append(voice_file)
            prev_char = char

        # ── OUTRO FRAME ──────────────────────────────────────────────
        if has_frame:
            parts.append(sil(OUTRO_PRE))
            parts.append(noted_path)
            parts.append(sil(OUTRO_POST))
        else:
            parts.append(sil(TAIL_PAD))

        # Write ffmpeg concat list
        concat_list = tmpdir / "concat.txt"
        concat_list.write_text(
            "\n".join(f"file '{p}'" for p in parts), encoding="utf-8"
        )

        run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(concat_list),
            "-c:a", "libmp3lame", "-b:a", "192k",
            "-ar", str(SAMPLE_RATE), "-ac", "2",
            str(output),
        ])

    dur = ffprobe_dur(output)
    size_mb = output.stat().st_size / 1024 / 1024
    print(f"  {ep_dir.name}: {int(dur//60)}:{dur%60:05.2f}  {size_mb:.1f} MB  ✓")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--series", choices=list(SERIES_EPISODES.keys()))
    parser.add_argument("--episode", type=int, choices=range(1, 7))
    args = parser.parse_args()

    if args.episode and not args.series:
        parser.error("--episode requires --series")

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            sys.exit(f"ERROR: {tool} not on PATH.")

    series_to_run = (
        {args.series: SERIES_EPISODES[args.series]}
        if args.series else SERIES_EPISODES
    )

    all_ok = True
    for series_key, eps in series_to_run.items():
        print(f"\n=== {series_key.upper().replace('_', ' ')} ===")
        if args.episode:
            eps = [eps[args.episode - 1]]
        for ep_num, ep_folder in enumerate(eps, 1):
            if args.episode:
                ep_num = args.episode
            ok = assemble_episode(SEASON2 / ep_folder, series_key, ep_num)
            if not ok:
                all_ok = False

    print("\nDone." if all_ok else "\nCompleted with errors — check output above.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
