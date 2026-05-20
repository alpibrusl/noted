"""Assemble AGREEABLE episodes 1-6 into final MP3s.

Episode 1 uses its hand-tuned assemble.py.
Episodes 2-6 use auto-generated timelines from their script.json files.

Usage:
    python3 assemble_all.py            # all episodes
    python3 assemble_all.py --episode 3
"""

from __future__ import annotations
import argparse, json, math, shutil, subprocess, sys
from pathlib import Path

HERE   = Path(__file__).resolve().parent
SR     = 44100
TAIL   = 5.0

# shared SFX / music — copied from ep1
SFX_SRC   = HERE / "agreeable_ep1" / "sfx"
MUSIC_SRC = HERE / "agreeable_ep1" / "music"


# ── silence heuristics ────────────────────────────────────────────────────────

def auto_timeline(script: list[dict]) -> list[tuple[str, float]]:
    """Return (line_id, pre_silence_sec) for every line."""
    timeline = []
    prev = None
    consec_narr = 0

    for i, entry in enumerate(script):
        char = entry["character"]
        lid  = entry["id"]

        if i == 0:
            pre = 0.5
        elif char == "ARIA":
            pre = 1.3
        elif prev == "NARRATOR" and char == "NARRATOR":
            consec_narr += 1
            pre = 0.6 if consec_narr < 3 else 0.4   # montage narration runs
        elif prev != "NARRATOR" and char == "NARRATOR":
            pre = 0.9   # entering narration from dialogue
        elif prev == "NARRATOR" and char != "NARRATOR":
            pre = 0.7   # out of narration into dialogue
        elif prev == char:
            pre = 0.3   # same speaker continuing
        else:
            pre = 0.5   # standard dialogue switch

        if prev != "NARRATOR":
            consec_narr = 0

        timeline.append((lid, pre))
        prev = char

    return timeline


# ── anchor resolution ─────────────────────────────────────────────────────────

class Anchor:
    def __init__(self, start: float, end: float):
        self.start = start
        self.end   = end


def build_anchors(timeline: list[tuple[str, float]],
                  voices_dir: Path) -> dict[str, Anchor]:
    anchors: dict[str, Anchor] = {}
    cursor = 0.0
    for lid, pre in timeline:
        path = voices_dir / f"{lid}.mp3"
        dur  = ffprobe_duration(path)
        anchors[lid] = Anchor(start=cursor + pre, end=cursor + pre + dur)
        cursor += pre + dur
    return anchors


def resolve(spec: tuple[str, str, float], anchors: dict[str, Anchor]) -> float:
    lid, edge, offset = spec
    a = anchors[lid]
    return max(0.0, (a.start if edge == "start" else a.end) + offset)


# ── smart BG / SFX placement ──────────────────────────────────────────────────

def make_bg_tracks(script: list[dict], sfx_dir: Path, music_dir: Path) -> list[dict]:
    """Generate BG_TRACKS adapted to this episode's line IDs."""
    ids   = [e["id"] for e in script]
    chars = {e["id"]: e["character"] for e in script}
    n     = len(ids)

    # Scene boundaries: first ARIA line, midpoint, last quarter
    aria_ids  = [i for i in ids if chars[i] == "ARIA"]
    narr_ids  = [i for i in ids if chars[i] == "NARRATOR"]
    first_id  = ids[0]
    last_id   = ids[-1]
    mid_narr  = narr_ids[len(narr_ids) // 2] if narr_ids else ids[n // 2]
    late_narr = narr_ids[int(len(narr_ids) * 0.72)] if len(narr_ids) > 4 else ids[int(n * 0.72)]

    def db(x: float) -> float:
        return 10 ** (x / 20.0)

    tracks = []

    # Office ambience: whole first ~70%
    if (sfx_dir / "office_ambience.mp3").exists():
        tracks.append({
            "file": sfx_dir / "office_ambience.mp3",
            "start":        (first_id,  "start", 0.0),
            "fade_in":      2.0,
            "fade_out_at":  (mid_narr,  "end",   0.0),
            "fade_out_dur": 2.0,
            "volume":       db(-25),
            "loop":         True,
        })

    # Cold-open piano: first narrator line only
    if narr_ids and (music_dir / "piano_melancholy.mp3").exists():
        tracks.append({
            "file": music_dir / "piano_melancholy.mp3",
            "start":        (first_id,  "start", 0.0),
            "fade_in":      2.0,
            "fade_out_at":  (narr_ids[min(2, len(narr_ids)-1)], "end", 0.0),
            "fade_out_dur": 2.0,
            "volume":       db(-22),
            "loop":         False,
        })

    # Server hum: late episode
    if (sfx_dir / "server_hum.mp3").exists():
        tracks.append({
            "file": sfx_dir / "server_hum.mp3",
            "start":        (late_narr, "start", -1.0),
            "fade_in":      2.0,
            "fade_out_at":  (last_id,   "end",   1.0),
            "fade_out_dur": 2.0,
            "volume":       db(-22),
            "loop":         True,
        })

    # Closing piano: final ~15%
    final_narr = narr_ids[int(len(narr_ids) * 0.82)] if len(narr_ids) > 4 else ids[int(n * 0.82)]
    if (music_dir / "piano_melancholy.mp3").exists():
        tracks.append({
            "file": music_dir / "piano_melancholy.mp3",
            "start":        (final_narr, "start", 0.0),
            "fade_in":      2.0,
            "fade_out_at":  (last_id,    "end",   2.0),
            "fade_out_dur": 4.0,
            "volume":       db(-22),
            "loop":         False,
        })

    return tracks


def make_sfx_hits(script: list[dict], sfx_dir: Path) -> list[dict]:
    """Place SFX one-shots at natural cue points."""
    ids   = [e["id"] for e in script]
    chars = {e["id"]: e["character"] for e in script}
    hits  = []

    aria_ids = [i for i in ids if chars[i] == "ARIA"]
    narr_ids = [i for i in ids if chars[i] == "NARRATOR"]

    # startup chime: after first narr block
    if len(narr_ids) >= 2 and (sfx_dir / "startup_chime.mp3").exists():
        hits.append({"file": sfx_dir / "startup_chime.mp3",
                     "at": (narr_ids[1], "end", 0.1), "volume": 0.55})

    # notification ping before first ARIA line
    if aria_ids and (sfx_dir / "notification_ping.mp3").exists():
        hits.append({"file": sfx_dir / "notification_ping.mp3",
                     "at": (aria_ids[0], "start", -0.3), "volume": 0.55})

    # second ping around 40% mark
    mid_aria = aria_ids[len(aria_ids) // 2] if len(aria_ids) > 1 else None
    if mid_aria and (sfx_dir / "notification_ping.mp3").exists():
        hits.append({"file": sfx_dir / "notification_ping.mp3",
                     "at": (mid_aria, "start", -0.2), "volume": 0.5})

    # keyboard typing at two narr lines in the middle
    mid_narr_idx = len(narr_ids) // 3
    for idx in [mid_narr_idx, mid_narr_idx * 2]:
        if idx < len(narr_ids) and (sfx_dir / "keyboard_typing.mp3").exists():
            hits.append({"file": sfx_dir / "keyboard_typing.mp3",
                         "at": (narr_ids[idx], "start", 0.4), "volume": 0.45})

    # mouse click after 2nd and 4th narr lines
    for idx in [2, 4]:
        if idx < len(narr_ids) and (sfx_dir / "mouse_click.mp3").exists():
            hits.append({"file": sfx_dir / "mouse_click.mp3",
                         "at": (narr_ids[idx], "end", 0.1), "volume": 0.65})

    # phone buzz at ~65% narr line
    buzz_idx = int(len(narr_ids) * 0.65)
    if buzz_idx < len(narr_ids) and (sfx_dir / "phone_buzz.mp3").exists():
        hits.append({"file": sfx_dir / "phone_buzz.mp3",
                     "at": (narr_ids[buzz_idx], "end", 0.15), "volume": 0.75})

    return hits


# ── ffmpeg helpers ────────────────────────────────────────────────────────────

def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        raise SystemExit(r.returncode)


def ffprobe_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


# ── pass 1: voice track ───────────────────────────────────────────────────────

def build_voices_track(timeline: list[tuple[str, float]],
                       voices_dir: Path, out: Path) -> dict[str, Anchor]:
    print(f"  Pass 1: {len(timeline)} lines")
    inputs, filter_parts, concat_labels = [], [], []
    anchors: dict[str, Anchor] = {}
    cursor = 0.0
    ni = 0

    for idx, (lid, pre) in enumerate(timeline):
        vpath = voices_dir / f"{lid}.mp3"
        inputs += ["-f", "lavfi", "-t", f"{pre:.3f}", "-i",
                   f"anullsrc=r={SR}:cl=stereo"]
        si = ni; ni += 1
        inputs += ["-i", str(vpath)]
        vi = ni; ni += 1

        sl, vl = f"s{idx}", f"v{idx}"
        for i_, l_ in [(si, sl), (vi, vl)]:
            filter_parts.append(
                f"[{i_}:a]aresample={SR},"
                f"aformat=sample_fmts=s16:channel_layouts=stereo[{l_}]")
        concat_labels += [f"[{sl}]", f"[{vl}]"]

        dur = ffprobe_duration(vpath)
        anchors[lid] = Anchor(start=cursor + pre, end=cursor + pre + dur)
        cursor += pre + dur

    # tail pad
    inputs += ["-f", "lavfi", "-t", f"{TAIL:.1f}", "-i",
               f"anullsrc=r={SR}:cl=stereo"]
    pi = ni
    filter_parts.append(
        f"[{pi}:a]aresample={SR},"
        f"aformat=sample_fmts=s16:channel_layouts=stereo[pad]")
    concat_labels.append("[pad]")

    n_streams = len(concat_labels)
    fc = ";".join(filter_parts) + ";" + "".join(concat_labels) + \
         f"concat=n={n_streams}:v=0:a=1[out]"

    out.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
        + inputs
        + ["-filter_complex", fc, "-map", "[out]", "-c:a", "pcm_s16le", str(out)])

    dur = ffprobe_duration(out)
    print(f"  voices_track.wav  {dur:.1f}s")
    return anchors


# ── pass 2: mix ───────────────────────────────────────────────────────────────

def mix(voices_track: Path, bg_tracks: list[dict], sfx_hits: list[dict],
        anchors: dict[str, Anchor], output: Path) -> None:
    print("  Pass 2: mixing")
    inputs  = ["-i", str(voices_track)]
    filters = []
    labels  = ["[0:a]"]
    ni      = 1

    avail_bg  = [t for t in bg_tracks  if t["file"].exists()]
    avail_sfx = [t for t in sfx_hits   if t["file"].exists()]

    for bg in avail_bg:
        st   = resolve(bg["start"],       anchors)
        fot  = resolve(bg["fade_out_at"], anchors)
        delay_ms = int(st * 1000)
        loop_args = ["-stream_loop", "-1"] if bg.get("loop") else []
        inputs += loop_args + ["-i", str(bg["file"])]
        lbl = f"bg{ni}"
        filters.append(
            f"[{ni}:a]aresample={SR},"
            f"aformat=sample_fmts=s16:channel_layouts=stereo,"
            f"volume={bg['volume']:.4f},"
            f"adelay={delay_ms}|{delay_ms},"
            f"afade=t=in:st={st:.3f}:d={bg['fade_in']:.3f},"
            f"afade=t=out:st={fot:.3f}:d={bg['fade_out_dur']:.3f}"
            f"[{lbl}]")
        labels.append(f"[{lbl}]"); ni += 1

    for sfx in avail_sfx:
        at = resolve(sfx["at"], anchors)
        delay_ms = int(at * 1000)
        inputs += ["-i", str(sfx["file"])]
        lbl = f"fx{ni}"
        filters.append(
            f"[{ni}:a]aresample={SR},"
            f"aformat=sample_fmts=s16:channel_layouts=stereo,"
            f"volume={sfx['volume']:.4f},"
            f"adelay={delay_ms}|{delay_ms}"
            f"[{lbl}]")
        labels.append(f"[{lbl}]"); ni += 1

    fc = (";".join(filters) + ";" if filters else "") + \
         "".join(labels) + \
         f"amix=inputs={len(labels)}:duration=first:normalize=0[out]"

    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
        + inputs
        + ["-filter_complex", fc, "-map", "[out]",
           "-c:a", "libmp3lame", "-b:a", "192k", "-ar", str(SR), "-ac", "2",
           str(output)])


# ── assemble one episode ──────────────────────────────────────────────────────

def assemble_episode(ep: int) -> None:
    ep_dir     = HERE / f"agreeable_ep{ep}"
    script     = json.loads((ep_dir / "script.json").read_text(encoding="utf-8"))
    voices_dir = ep_dir / "voices"
    build_dir  = ep_dir / "build"
    sfx_dir    = ep_dir / "sfx"
    music_dir  = ep_dir / "music"
    vtrack     = build_dir / "voices_track.wav"
    output     = ep_dir / f"episode_{ep:02d}.mp3"

    # ensure SFX/music are present (copy from ep1 if not)
    for src_dir, dst_dir in [(SFX_SRC, sfx_dir), (MUSIC_SRC, music_dir)]:
        if src_dir.exists():
            dst_dir.mkdir(parents=True, exist_ok=True)
            for f in src_dir.glob("*.mp3"):
                dst = dst_dir / f.name
                if not dst.exists():
                    shutil.copy2(f, dst)

    # check voices
    missing = [e["id"] for e in script
               if not (voices_dir / f"{e['id']}.mp3").exists()]
    if missing:
        print(f"  ERROR: missing voices: {missing[:5]}{'...' if len(missing)>5 else ''}")
        return

    timeline   = auto_timeline(script)
    anchors    = build_voices_track(timeline, voices_dir, vtrack)
    bg_tracks  = make_bg_tracks(script, sfx_dir, music_dir)
    sfx_hits   = make_sfx_hits(script, sfx_dir)
    mix(vtrack, bg_tracks, sfx_hits, anchors, output)

    dur  = ffprobe_duration(output)
    mins = int(dur // 60); secs = dur - mins * 60
    mb   = output.stat().st_size / 1024 / 1024
    print(f"  -> {output.name}  {mins}:{secs:05.2f}  {mb:.1f} MB")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", type=int, choices=range(1, 7))
    args = parser.parse_args()

    episodes = [args.episode] if args.episode else list(range(1, 7))

    for ep in episodes:
        print(f"\n=== Episode {ep} ===")
        if ep == 1:
            # ep1 has its own hand-tuned assemble.py
            r = subprocess.run(
                ["python3.12", str(HERE / "agreeable_ep1" / "assemble.py")],
                cwd=HERE / "agreeable_ep1")
            if r.returncode != 0:
                print("  ep1 assemble.py failed")
        else:
            assemble_episode(ep)

    print("\nDone.")


if __name__ == "__main__":
    main()
