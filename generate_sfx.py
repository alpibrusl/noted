"""Synthesise placeholder SFX and music for AGREEABLE ep1 using numpy + ffmpeg.

Generates:
  agreeable_ep1/sfx/  office_ambience.mp3  server_hum.mp3  apartment_ambience.mp3
                      startup_chime.mp3    notification_ping.mp3  mouse_click.mp3
                      keyboard_typing.mp3  phone_buzz.mp3
  agreeable_ep1/music/ piano_melancholy.mp3

No external dependencies beyond numpy and ffmpeg (already installed).
"""

from __future__ import annotations
import subprocess, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
EP1  = HERE / "agreeable_ep1"
SR   = 44100


# ── helpers ──────────────────────────────────────────────────────────────────

def write_mp3(sig: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if sig.ndim == 1:
        sig = np.stack([sig, sig], axis=1)
    pcm = (np.clip(sig, -1.0, 1.0) * 32767).astype(np.int16)
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "pipe:0",
         "-c:a", "libmp3lame", "-b:a", "128k", str(path)],
        input=pcm.tobytes(), check=True,
    )
    print(f"  {path.relative_to(HERE)}  ({path.stat().st_size // 1024} KB)")


def norm(sig: np.ndarray, peak: float = 0.85) -> np.ndarray:
    m = np.max(np.abs(sig))
    return sig * (peak / m) if m > 1e-9 else sig


def fade(sig: np.ndarray, fi: float = 0.02, fo: float = 0.05) -> np.ndarray:
    sig = sig.copy()
    ni, no = int(SR * fi), int(SR * fo)
    if ni: sig[:ni]  *= np.linspace(0, 1, ni)
    if no: sig[-no:] *= np.linspace(1, 0, no)
    return sig


def bandpass(sig: np.ndarray, lo: float = 0, hi: float = 22000) -> np.ndarray:
    spec  = np.fft.rfft(sig)
    freqs = np.fft.rfftfreq(len(sig), 1 / SR)
    spec[freqs < lo] = 0
    spec[freqs > hi] = 0
    return np.fft.irfft(spec, len(sig))


def pink(duration: float, seed: int = 0) -> np.ndarray:
    n     = int(SR * duration)
    white = np.random.default_rng(seed).standard_normal(n)
    spec  = np.fft.rfft(white)
    f     = np.fft.rfftfreq(n, 1 / SR); f[0] = 1
    spec /= np.sqrt(f)
    return norm(np.fft.irfft(spec, n))


def tone(freq: float, dur: float, decay: float = 5.0,
         harmonics: tuple = ((1, 1.0), (2, 0.3), (3, 0.1), (4, 0.04))) -> np.ndarray:
    t   = np.arange(int(SR * dur)) / SR
    env = np.exp(-decay * t)
    sig = sum(a * np.sin(2 * np.pi * freq * h * t) for h, a in harmonics)
    return sig * env


# ── ambiences (30 s loops) ────────────────────────────────────────────────────

def office_ambience() -> np.ndarray:
    dur = 30.0
    n   = int(SR * dur)
    t   = np.arange(n) / SR
    # low-cut pink noise (room tone feel, no hiss)
    body  = bandpass(pink(dur, seed=1), lo=120, hi=2000)
    # very faint presence layer just above speech range
    air   = bandpass(pink(dur, seed=5), lo=2000, hi=3500) * 0.08
    hum   = 0.03 * np.sin(2 * np.pi * 60 * t) + 0.015 * np.sin(2 * np.pi * 120 * t)
    return fade(norm(body * 0.75 + air + hum) * 0.75)


def server_hum() -> np.ndarray:
    dur = 30.0
    n   = int(SR * dur)
    t   = np.arange(n) / SR
    hum = (0.50 * np.sin(2 * np.pi *  60 * t) +
           0.30 * np.sin(2 * np.pi * 120 * t) +
           0.15 * np.sin(2 * np.pi * 180 * t) +
           0.08 * np.sin(2 * np.pi * 240 * t))
    noise = bandpass(pink(dur, seed=2), lo=30, hi=400)
    return fade(norm(hum + noise * 0.15))


def apartment_ambience() -> np.ndarray:
    dur = 30.0
    n   = int(SR * dur)
    t   = np.arange(n) / SR
    noise  = bandpass(pink(dur, seed=3), lo=50, hi=1500)
    rumble = 0.08 * np.sin(2 * np.pi * 70 * t) * np.sin(2 * np.pi * 0.25 * t)
    return fade(norm(noise * 0.6 + rumble) * 0.45)


# ── SFX hits ──────────────────────────────────────────────────────────────────

def startup_chime() -> np.ndarray:
    notes  = [523.25, 659.25, 783.99, 1046.50]  # C5 E5 G5 C6
    step   = 0.18
    total  = int(SR * (step * len(notes) + 0.9))
    sig    = np.zeros(total)
    for i, f in enumerate(notes):
        t = tone(f, 1.0, decay=4.0, harmonics=((1, 0.6), (2, 0.25), (3, 0.08)))
        s = int(i * step * SR)
        e = min(s + len(t), total)
        sig[s:e] += t[:e - s]
    return fade(norm(sig) * 0.8, fi=0.005, fo=0.15)


def notification_ping() -> np.ndarray:
    sig = tone(880.0, 0.8, decay=5.5, harmonics=((1, 0.7), (2, 0.2), (3, 0.05)))
    return fade(norm(sig) * 0.8, fi=0.003, fo=0.06)


def mouse_click() -> np.ndarray:
    n   = int(SR * 0.08)
    rng = np.random.default_rng(10)
    sig = bandpass(rng.standard_normal(n), lo=1000, hi=8000)
    env = np.exp(-50 * np.arange(n) / SR)
    return fade(norm(sig * env) * 0.7, fi=0.001, fo=0.01)


def keyboard_typing() -> np.ndarray:
    total = int(SR * 0.65)
    sig   = np.zeros(total)
    rng   = np.random.default_rng(20)
    for offset in [0.0, 0.12, 0.25, 0.35]:
        n     = int(SR * 0.065)
        click = bandpass(rng.standard_normal(n), lo=700, hi=6000)
        env   = np.exp(-55 * np.arange(n) / SR)
        click = norm(click * env) * 0.55
        s     = int(offset * SR)
        sig[s:s + n] += click
    return fade(norm(sig) * 0.75, fi=0.001, fo=0.05)


def phone_buzz() -> np.ndarray:
    total = int(SR * 0.75)
    sig   = np.zeros(total)
    for offset in [0.0, 0.13, 0.26]:
        n   = int(SR * 0.09)
        t   = np.arange(n) / SR
        pulse = bandpass(np.sign(np.sin(2 * np.pi * 200 * t)), lo=80, hi=900)
        env  = np.exp(-18 * t)
        s    = int(offset * SR)
        sig[s:s + n] += pulse * env * 0.5
    return fade(norm(sig) * 0.85, fi=0.001, fo=0.05)


# ── music ─────────────────────────────────────────────────────────────────────

def piano_melancholy() -> np.ndarray:
    """Am–F–C–Em arpeggiated at 72 BPM, ~2.5 min."""
    BPM   = 72
    EIGHT = 60.0 / BPM / 2          # 8th-note duration in seconds

    # chord notes (Hz): root, 3rd, 5th
    Am = [220.00, 261.63, 329.63]   # A3 C4 E4
    F  = [174.61, 220.00, 261.63]   # F3 A3 C4
    C  = [130.81, 164.81, 196.00]   # C3 E3 G3
    Em = [164.81, 196.00, 246.94]   # E3 G3 B3

    def arp(chord: list[float]) -> list[tuple[float, float]]:
        pattern = [0, 1, 2, 1, 0, 1, 2, 1]
        return [(chord[i], EIGHT) for i in pattern]

    sequence = arp(Am) + arp(F) + arp(C) + arp(Em)   # one 4-bar phrase

    phrase_dur = len(sequence) * EIGHT                # ~13.3 s
    target_dur = 150.0                                # 2.5 min
    repeats    = int(np.ceil(target_dur / phrase_dur))

    # pre-render each unique frequency (tone duration = 8th + 1.5 s decay tail)
    cache: dict[float, np.ndarray] = {}
    for freq, _ in sequence:
        if freq not in cache:
            cache[freq] = tone(freq, EIGHT + 1.5, decay=3.5,
                               harmonics=((1, 0.5), (2, 0.28), (3, 0.12), (4, 0.05)))

    total_n = int(SR * target_dur) + int(SR * 2)
    sig     = np.zeros(total_n)
    cursor  = 0

    for _ in range(repeats):
        for freq, dur in sequence:
            if cursor >= total_n:
                break
            t = cache[freq]
            e = min(cursor + len(t), total_n)
            sig[cursor:e] += t[:e - cursor] * 0.65
            cursor += int(dur * SR)

    sig = sig[:int(SR * target_dur)]

    # 3 s fade-in, 5 s fade-out
    fi, fo = int(SR * 3), int(SR * 5)
    sig[:fi]  *= np.linspace(0, 1, fi)
    sig[-fo:] *= np.linspace(1, 0, fo)
    return norm(sig) * 0.82


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    sfx   = EP1 / "sfx"
    music = EP1 / "music"

    print("Generating SFX...")
    write_mp3(office_ambience(),    sfx   / "office_ambience.mp3")
    write_mp3(server_hum(),         sfx   / "server_hum.mp3")
    write_mp3(apartment_ambience(), sfx   / "apartment_ambience.mp3")
    write_mp3(startup_chime(),      sfx   / "startup_chime.mp3")
    write_mp3(notification_ping(),  sfx   / "notification_ping.mp3")
    write_mp3(mouse_click(),        sfx   / "mouse_click.mp3")
    write_mp3(keyboard_typing(),    sfx   / "keyboard_typing.mp3")
    write_mp3(phone_buzz(),         sfx   / "phone_buzz.mp3")

    print("Generating music...")
    write_mp3(piano_melancholy(),   music / "piano_melancholy.mp3")

    print("\nDone. Run:  cd agreeable_ep1 && python3.12 assemble.py")


if __name__ == "__main__":
    main()
