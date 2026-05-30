"""Generate NOTED intro/outro audio pieces for all series.

Produces:
  intros/noted.mp3               — "NOTED."  (shared, used twice per episode)
  intros/compliant_ep{1-6}.mp3   — "COMPLIANT. Episode one." etc.
  intros/eight_minutes_ep{1-6}.mp3
  intros/null_pointer_ep{1-6}.mp3
  intros/deprecated_ep{1-6}.mp3

All spoken by bm_george. Requires Kokoro: pip install 'podcastkit[kokoro]'
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent   # noted/
INTROS_DIR = ROOT / "intros"
KOKORO_SAMPLE_RATE = 24000
VOICE = "bm_george"

EP_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}

SERIES_TITLES = {
    "compliant":               "COMPLIANT",
    "eight_minutes":           "EIGHT MINUTES",
    "null_pointer":            "NULL POINTER",
    "deprecated":              "DEPRECATED",
    "separation_of_concerns":  "SEPARATION OF CONCERNS",
}

_pipeline = None


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        from kokoro import KPipeline
        _pipeline = KPipeline(lang_code="b")  # bm_george is British
    return _pipeline


def write_mp3(audio: np.ndarray, dest: Path) -> None:
    if shutil.which("ffmpeg") is None:
        sys.exit("ERROR: ffmpeg not on PATH.")
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16).tobytes()
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "s16le", "-ar", str(KOKORO_SAMPLE_RATE), "-ac", "1", "-i", "pipe:0",
        "-c:a", "libmp3lame", "-b:a", "192k", "-ar", "44100", "-ac", "2",
        str(dest),
    ]
    subprocess.run(cmd, input=pcm, check=True)


def synthesize(text: str, dest: Path) -> None:
    pipeline = get_pipeline()
    chunks = []
    for _, _, audio in pipeline(text, voice=VOICE):
        chunks.append(audio.cpu().numpy() if hasattr(audio, "cpu") else np.asarray(audio))
    if not chunks:
        raise RuntimeError(f"No audio for: {text!r}")
    write_mp3(np.concatenate(chunks), dest)


def main() -> int:
    INTROS_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating NOTED intro/outro pieces...")

    # Shared "NOTED." stamp — used as both intro tag and outro closer
    noted_path = INTROS_DIR / "noted.mp3"
    if noted_path.exists():
        print(f"  noted.mp3  skip")
    else:
        print(f"  noted.mp3  generating...")
        synthesize("NOTED.", noted_path)
        print(f"  noted.mp3  done")

    # Per-series, per-episode title lines
    for series_key, title in SERIES_TITLES.items():
        for ep_num in range(1, 7):
            fname = f"{series_key}_ep{ep_num}.mp3"
            dest = INTROS_DIR / fname
            if dest.exists():
                print(f"  {fname}  skip")
                continue
            text = f"{title}. Episode {EP_WORDS[ep_num]}."
            print(f"  {fname}  {text!r}")
            synthesize(text, dest)

    print("\nAll intro/outro pieces ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
