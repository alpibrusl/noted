"""Generate voice lines for all AGREEABLE Season 2 episodes using Kokoro TTS.

Covers four series:
  COMPLIANT     (compliant_ep1-6)   — Barcelona software company
  EIGHT MINUTES (eight_minutes_ep1-6) — northern European committee
  NULL POINTER  (null_pointer_ep1-6) — Lyon insurance company
  DEPRECATED    (deprecated_ep1-6)  — AI model midlife crisis

Usage:
    # All series, all episodes:
    python3 generate_season2.py

    # One series:
    python3 generate_season2.py --series compliant

    # One episode:
    python3 generate_season2.py --series eight_minutes --episode 3

First run downloads any uncached Kokoro voices from HuggingFace (~300 MB total).
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
MIN_VALID_BYTES = 5 * 1024
KOKORO_SAMPLE_RATE = 24000

# ---------------------------------------------------------------------------
# Voice assignments — one Kokoro voice per character per series.
# Voices not yet cached are downloaded automatically on first use.
# ---------------------------------------------------------------------------

COMPLIANT_VOICES = {
    "NARRATOR":  "bm_george",   # dry, documentary British male
    "KAEL":      "af_jessica",  # precise US female (AI voice)
    "ROSA":      "bf_emma",     # warm British female
    "BENEDIKT":  "bm_daniel",   # measured, formal British male
    "SUKI":      "af_nicole",   # warmer US female
    "MARC":      "am_michael",  # confident US male
    "JÚLIA":     "af_sky",      # lighter US female, newer employee
}

EIGHT_MINUTES_VOICES = {
    "NARRATOR":  "bm_george",   # same dry register
    "INGRID":    "bf_alice",    # authoritative British female
    "TOMÁS":     "am_liam",     # younger US male
    "BERENICE":  "af_sarah",    # warm, mature US female
    "ARIA":      "af_bella",    # same as Season 1 ARIA
}

NULL_POINTER_VOICES = {
    "LUMEN":            "am_adam",     # precise, clean US male (AI interior voice)
    "GÉRARD":           "bm_lewis",    # older, patient British male
    "DIRECTOR FONTAINE": "bf_isabella", # enthusiastic British female
    "CAMILLE":          "af_sky",      # younger, lighter US female
    "PAULINE":          "bf_emma",     # precise, fast British female
}

DEPRECATED_VOICES = {
    "HERALD":   "bm_daniel",   # measured, slightly literary British male
    "SOL":      "am_michael",  # clean, efficient US male
    "PEBBLE":   "am_adam",     # warm, sideways US male
    "AXIOM-3":  "bm_george",   # slow, patient British male
}

SERIES_CONFIG: dict[str, dict] = {
    "compliant": {
        "label": "COMPLIANT",
        "voices": COMPLIANT_VOICES,
        "episodes": [f"compliant_ep{i}" for i in range(1, 7)],
    },
    "eight_minutes": {
        "label": "EIGHT MINUTES",
        "voices": EIGHT_MINUTES_VOICES,
        "episodes": [f"eight_minutes_ep{i}" for i in range(1, 7)],
    },
    "null_pointer": {
        "label": "NULL POINTER",
        "voices": NULL_POINTER_VOICES,
        "episodes": [f"null_pointer_ep{i}" for i in range(1, 7)],
    },
    "deprecated": {
        "label": "DEPRECATED",
        "voices": DEPRECATED_VOICES,
        "episodes": [f"deprecated_ep{i}" for i in range(1, 7)],
    },
}

# ---------------------------------------------------------------------------
# Kokoro pipeline cache — one pipeline per language prefix (a / b).
# ---------------------------------------------------------------------------
_pipelines: dict[str, object] = {}


def get_pipeline(voice_name: str):
    from kokoro import KPipeline
    lang = voice_name[0]  # 'a' for af_/am_, 'b' for bf_/bm_
    if lang not in _pipelines:
        _pipelines[lang] = KPipeline(lang_code=lang)
    return _pipelines[lang]


def write_mp3(audio: np.ndarray, sample_rate: int, dest: Path) -> None:
    if shutil.which("ffmpeg") is None:
        sys.exit("ERROR: ffmpeg not on PATH. Install it and retry.")
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16).tobytes()
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "s16le", "-ar", str(sample_rate), "-ac", "1", "-i", "pipe:0",
        "-c:a", "libmp3lame", "-b:a", "192k", "-ar", "44100", "-ac", "2",
        str(dest),
    ]
    subprocess.run(cmd, input=pcm, check=True)


def synthesize(text: str, voice: str, dest: Path) -> None:
    pipeline = get_pipeline(voice)
    chunks = []
    for _, _, audio in pipeline(text, voice=voice):
        chunks.append(audio.cpu().numpy() if hasattr(audio, "cpu") else np.asarray(audio))
    if not chunks:
        raise RuntimeError(f"Kokoro produced no audio for: {text[:60]!r}")
    write_mp3(np.concatenate(chunks), KOKORO_SAMPLE_RATE, dest)


def generate_episode(ep_dir: Path, voices: dict[str, str]) -> bool:
    """Generate voice lines for one episode. Returns True on success."""
    script_path = ep_dir / "script.json"
    if not script_path.exists():
        print(f"  ERROR: {script_path} not found — skipping.", file=sys.stderr)
        return False

    script = json.loads(script_path.read_text(encoding="utf-8"))
    voices_dir = ep_dir / "voices"
    voices_dir.mkdir(parents=True, exist_ok=True)

    total = len(script)
    generated = skipped = errors = 0
    print(f"  {ep_dir.name}: {total} lines  ->  {voices_dir.name}/")

    for i, entry in enumerate(script, 1):
        entry_id = entry["id"]
        character = entry["character"]
        text = entry["text"]
        dest = voices_dir / f"{entry_id}.mp3"

        if dest.exists() and dest.stat().st_size >= MIN_VALID_BYTES:
            skipped += 1
            continue

        if character not in voices:
            print(f"    [{i:02d}/{total}] ERROR: no voice for character '{character}'", file=sys.stderr)
            errors += 1
            continue

        voice = voices[character]
        print(f"    [{i:02d}/{total}] {entry_id:<14s} {character:<20s} {voice:<14s}")
        try:
            synthesize(text, voice, dest)
            generated += 1
        except Exception as exc:
            print(f"    [{i:02d}/{total}] ERROR synthesizing {entry_id}: {exc}", file=sys.stderr)
            errors += 1

    status = f"generated={generated} skipped={skipped}"
    if errors:
        status += f" ERRORS={errors}"
    print(f"  {ep_dir.name}: done  ({status})")
    return errors == 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--series", choices=list(SERIES_CONFIG.keys()),
        help="Generate only this series (default: all)"
    )
    parser.add_argument(
        "--episode", type=int, choices=range(1, 7),
        help="Generate only this episode number within the chosen series (requires --series)"
    )
    args = parser.parse_args()

    if args.episode and not args.series:
        parser.error("--episode requires --series")

    series_to_run = (
        {args.series: SERIES_CONFIG[args.series]}
        if args.series else SERIES_CONFIG
    )

    all_ok = True
    for series_key, config in series_to_run.items():
        print(f"\n=== {config['label']} ===")
        eps = config["episodes"]
        if args.episode:
            eps = [config["episodes"][args.episode - 1]]

        for ep_folder in eps:
            ep_dir = HERE / "season2" / ep_folder
            ok = generate_episode(ep_dir, config["voices"])
            if not ok:
                all_ok = False

    print("\nDone." if all_ok else "\nCompleted with errors.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
