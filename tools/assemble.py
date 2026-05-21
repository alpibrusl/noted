"""Assemble NOTED episode voice lines into a single MP3 per episode.

Wraps each episode with the NOTED frame (noted.mp3 → series title → content → noted.mp3).
Reads script.json and voices/{id}.mp3 from each episode directory.

Requires: ffmpeg on PATH, intros/ generated (run tools/generate_intros.py first).

Usage:
    python3 tools/assemble.py                          # all series
    python3 tools/assemble.py --series compliant       # one series
    python3 tools/assemble.py --series deprecated --episode 6
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent   # noted/
INTROS_DIR = ROOT / "intros"
SAMPLE_RATE = 44100

SILENCE_BETWEEN = 0.55      # default inter-line gap
SILENCE_PARAGRAPH = 1.1     # longer gap at narrator/character transitions
TAIL_PAD = 3.0              # silence at end when no NOTED frame

INTRO_PRE   = 1.2   # silence before opening "NOTED."
INTRO_MID   = 0.9   # silence between "NOTED." and series title
INTRO_POST  = 1.6   # silence between series title and first line
OUTRO_PRE   = 1.8   # silence after last line before closing "NOTED."
OUTRO_POST  = 2.5   # silence after closing "NOTED."

NARRATOR_CHARS = {"NARRATOR", "NARRADOR", "LUMEN", "HERALD"}

SERIES: dict[str, list[Path]] = {
    series: [ROOT / series / f"ep{i:02d}" for i in range(1, 7)]
    for series in ("compliant", "eight_minutes", "null_pointer", "deprecated")
}
# Single-pilot series.
SERIES["quijote"] = [ROOT / "quijote" / "ep01"]


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
    dest = tmpdir / f"sil_{idx:04d}.mp3"
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-t", f"{duration:.3f}",
        "-i", f"anullsrc=r={SAMPLE_RATE}:cl=stereo",
        "-c:a", "libmp3lame", "-b:a", "192k",
        "-ar", str(SAMPLE_RATE), "-ac", "2",
        str(dest),
    ])
    return dest


def check_intros(series_key: str, ep_num: int) -> tuple[Path, Path, Path] | None:
    noted = INTROS_DIR / "noted.mp3"
    title = INTROS_DIR / f"{series_key}_ep{ep_num}.mp3"
    if not noted.exists():
        print(f"  WARNING: {noted} missing — run tools/generate_intros.py first", file=sys.stderr)
        return None
    if not title.exists():
        print(f"  WARNING: {title} missing — run tools/generate_intros.py first", file=sys.stderr)
        return None
    return noted, title, noted


def assemble_episode(ep_dir: Path, series_key: str, ep_num: int) -> bool:
    script_path = ep_dir / "script.json"
    voices_dir = ep_dir / "voices"
    if not script_path.exists():
        print(f"  {ep_dir.name}: no script.json — skipped", file=sys.stderr)
        return False

    script = json.loads(script_path.read_text(encoding="utf-8"))

    missing = [e["id"] for e in script if not (voices_dir / f"{e['id']}.mp3").exists()]
    if missing:
        print(f"  {ep_dir.name}: missing voice files — run: podcastkit generate -e {ep_dir}", file=sys.stderr)
        return False

    intro_pieces = check_intros(series_key, ep_num)
    has_frame = intro_pieces is not None
    noted_path, title_path, _ = intro_pieces if has_frame else (None, None, None)

    output = ep_dir / f"episode_{ep_num:02d}.mp3"
    print(f"  {ep_dir}  →  {output.name}{'  [NOTED frame]' if has_frame else '  [no frame]'}")

    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        parts: list[Path] = []
        sil_idx = 0

        def sil(dur: float) -> Path:
            nonlocal sil_idx
            p = silence_file(dur, tmpdir, sil_idx)
            sil_idx += 1
            return p

        if has_frame:
            parts.append(sil(INTRO_PRE))
            parts.append(noted_path)
            parts.append(sil(INTRO_MID))
            parts.append(title_path)
            parts.append(sil(INTRO_POST))

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

        if has_frame:
            parts.append(sil(OUTRO_PRE))
            parts.append(noted_path)
            parts.append(sil(OUTRO_POST))
        else:
            parts.append(sil(TAIL_PAD))

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
    parser.add_argument("--series", choices=list(SERIES.keys()))
    parser.add_argument("--episode", type=int, choices=range(1, 7))
    args = parser.parse_args()

    if args.episode and not args.series:
        parser.error("--episode requires --series")

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            sys.exit(f"ERROR: {tool} not on PATH.")

    series_to_run = {args.series: SERIES[args.series]} if args.series else SERIES

    all_ok = True
    for series_key, eps in series_to_run.items():
        print(f"\n=== {series_key.upper().replace('_', ' ')} ===")
        ep_list = [eps[args.episode - 1]] if args.episode else eps
        for ep_num, ep_dir in enumerate(ep_list, start=args.episode or 1):
            ok = assemble_episode(ep_dir, series_key, ep_num)
            if not ok:
                all_ok = False

    print("\nDone." if all_ok else "\nCompleted with errors.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
