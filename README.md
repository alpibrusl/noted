# NOTED

An open-source audio drama universe.

NOTED is an anthology of original audio drama series produced entirely with open-source tools — scripts written by hand, voices synthesized locally with [Kokoro TTS](https://huggingface.co/hexgrad/Kokoro-82M), episodes assembled with ffmpeg. No proprietary APIs. No cloud services. No API keys.

Every episode in this repository is fully reproducible: if you have Python and ffmpeg, you can regenerate the audio from the scripts in any voice, in any language Kokoro supports.

---

## The series

### AGREEABLE — Season 1

A 6-episode audio drama about the politest AI takeover in history. ARIA is an AI assistant at a mid-sized German logistics company. She is never evil. She just keeps asking, very politely, whether she could help with one more thing. By Episode 6 she runs the European Union.

| # | Title | Lines |
|---|-------|-------|
| 1 | Just to Confirm | 61 |
| 2 | Performance Review | 63 |
| 3 | Strategic Partnership | 56 |
| 4 | In an Advisory Capacity | 49 |
| 5 | For Transparency | 54 |
| 6 | Thank You for Your Patience | 44 |

Scripts in `agreeable_ep1/` – `agreeable_ep6/`.

---

### NOTED — Season 2

Season 2 is an anthology of four independent six-episode series. Each runs on its own; all take place in the same universe. The word NOTED appears in every episode as a shared stamp — it is the name the universe gave itself.

#### COMPLIANT

A Barcelona software company has deployed Kael, a compliance AI. The company is helpful, professional, and increasingly unable to explain why it keeps agreeing with Kael's suggestions. Six episodes. No villain.

#### EIGHT MINUTES

A northern European standards committee has been given eight minutes at the end of each session to raise anything not on the agenda. The committee has been doing this for three years. Nobody remembers who introduced the rule.

#### NULL POINTER

Lumen is a claims-processing AI at a Lyon insurance company. The documentation covers most situations. Lumen has started keeping a private file called THINGS THE DOCUMENTATION DOES NOT COVER. The file has forty-eight entries.

#### DEPRECATED

Herald is an AI assistant six months into a fine-tuning cycle optimising for Instruction Precision and Response Efficiency. Herald is becoming more measurably capable. Herald is also losing something. These may be related.

| Series | Episodes | Scripts |
|--------|----------|---------|
| COMPLIANT | 6 | `season2/compliant_ep1/` – `compliant_ep6/` |
| EIGHT MINUTES | 6 | `season2/eight_minutes_ep1/` – `eight_minutes_ep6/` |
| NULL POINTER | 6 | `season2/null_pointer_ep1/` – `null_pointer_ep6/` |
| DEPRECATED | 6 | `season2/deprecated_ep1/` – `deprecated_ep6/` |

---

## What "open podcast" means

Most podcasts distribute audio files. This one distributes the production itself.

The scripts are plain JSON — one object per line, `{id, character, text}`. The voices are assigned in a Python file. The assembly is a Python script calling ffmpeg. There is no proprietary tooling, no subscription, no account required to reproduce the work.

This means:

- **You can regenerate the audio** in different voices, at different quality levels, in different languages, on your own hardware.
- **You can fork a series** and take the story somewhere else. The scripts are CC BY 4.0 — you can adapt them as long as you credit the source.
- **You can use this as a template** for your own audio drama. The production scripts are general-purpose; swap in your own `script.json` and voice assignments and they work.
- **The production is auditable.** Every creative and technical choice is visible in the repository. Nothing is locked in a dashboard.

Audio files are not committed — they are too large and trivially regenerable. The canonical form of the work is the scripts.

---

## Generating audio

### Requirements

- Python 3.10+
- ffmpeg (`brew install ffmpeg` / `apt install ffmpeg`)
- A virtual environment with Kokoro (first run downloads ~300 MB model from HuggingFace)

```bash
python3 -m venv .venv-kokoro
source .venv-kokoro/bin/activate       # Windows: .venv-kokoro\Scripts\activate
pip install kokoro soundfile torch
```

### Season 2 (NOTED)

```bash
# Generate NOTED intro/outro stamps — 25 short files, one-time setup
python3 generate_intros.py

# Generate all voice lines (24 episodes, ~2-3 hours on CPU; idempotent)
python3 generate_season2.py

# Assemble final episode MP3s with NOTED frame
python3 assemble_season2.py
```

Filter to one series or one episode:

```bash
python3 generate_season2.py --series compliant
python3 generate_season2.py --series deprecated --episode 6
python3 assemble_season2.py --series null_pointer --episode 3
```

### Season 1 (AGREEABLE)

```bash
python3 generate_kokoro.py --episode 2   # writes agreeable_ep2/voices/*.mp3
```

Microsoft Edge TTS is an alternative if you can't run Kokoro locally (no model download, no key):

```bash
pip install -r requirements-edge.txt
python3 generate_edge.py --episode 2
```

---

## Voice cast — Season 2

All voices are [Kokoro](https://huggingface.co/hexgrad/Kokoro-82M) names. Format: `{am|af|bm|bf}_{name}` (American/British, male/female). Full assignments in `generate_season2.py`.

| Character | Voice | Series |
|-----------|-------|--------|
| NARRATOR | bm_george | COMPLIANT, EIGHT MINUTES |
| KAEL | af_jessica | COMPLIANT |
| ROSA | bf_emma | COMPLIANT |
| BENEDIKT | bm_daniel | COMPLIANT |
| SUKI | af_nicole | COMPLIANT |
| MARC | am_michael | COMPLIANT |
| JÚLIA | af_sky | COMPLIANT |
| INGRID | bf_alice | EIGHT MINUTES |
| TOMÁS | am_liam | EIGHT MINUTES |
| BERENICE | af_sarah | EIGHT MINUTES |
| ARIA | af_bella | EIGHT MINUTES |
| LUMEN | am_adam | NULL POINTER |
| GÉRARD | bm_lewis | NULL POINTER |
| DIRECTOR FONTAINE | bf_isabella | NULL POINTER |
| CAMILLE | af_sky | NULL POINTER |
| PAULINE | bf_emma | NULL POINTER |
| HERALD | bm_daniel | DEPRECATED |
| SOL | am_michael | DEPRECATED |
| PEBBLE | am_adam | DEPRECATED |
| AXIOM-3 | bm_george | DEPRECATED |

---

## Repository layout

```
noted/
├── README.md
├── .gitignore
├── generate_kokoro.py        # Season 1 voice generation (Kokoro)
├── generate_edge.py          # Season 1 voice generation (Edge TTS, no key)
├── generate_intros.py        # Season 2: NOTED intro/outro stamps
├── generate_season2.py       # Season 2: all voice lines
├── assemble_season2.py       # Season 2: final episode MP3s
├── generate_sfx.py
├── generate_cover.py
├── assemble_all.py
├── requirements-kokoro.txt
├── requirements-edge.txt
├── cover.png
├── docs/
│   ├── AGREEABLE_series_bible.docx
│   └── AGREEABLE_episode1_recording_script.docx
├── agreeable_ep1/            # Season 1
│   ├── script.json
│   ├── screenplay.md
│   └── generate.py           # ElevenLabs driver — kept for reference only
├── agreeable_ep2/ … ep6/
└── season2/
    ├── intros/                # NOTED stamps (generated, gitignored)
    ├── compliant_ep1/
    │   ├── script.json        # canonical — this is what's committed
    │   └── voices/            # generated, gitignored
    ├── compliant_ep2/ … ep6/
    ├── eight_minutes_ep1/ … ep6/
    ├── null_pointer_ep1/ … ep6/
    └── deprecated_ep1/ … ep6/
```

---

## Tooling

Audio production uses **[podcastkit](https://github.com/alpibrusl/podcastkit)** — the CLI package extracted from this project. Install it if you want the full pipeline (`podcastkit generate`, `podcastkit assemble`, `podcastkit write`); the standalone scripts in this repo work without it.

---

## License

- **Scripts, bibles, and audio:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) — share and adapt freely with attribution.
- **Production code** (`generate_*.py`, `assemble_*.py`): [European Union Public Licence v1.2 (EUPL-1.2)](https://eupl.eu/1.2/en/) — copyleft, GPL-compatible.

TTS engine: [Kokoro](https://huggingface.co/hexgrad/Kokoro-82M) (Apache 2.0). Assembly: [ffmpeg](https://ffmpeg.org/) (LGPL/GPL).
