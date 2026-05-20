# NOTED

An open-source audio drama universe.

NOTED is an anthology of original audio drama series produced entirely with open-source tools — scripts written by hand, voices synthesized locally with [Kokoro TTS](https://huggingface.co/hexgrad/Kokoro-82M), episodes assembled with ffmpeg. No proprietary APIs. No cloud services. No API keys.

Every episode in this repository is fully reproducible: if you have Python and ffmpeg, you can regenerate the audio from the scripts in any voice, in any language Kokoro supports.

Tooling: **[podcastkit](https://github.com/alpibrusl/podcastkit)** — the CLI extracted from this project.

---

## The series

### AGREEABLE

A 6-episode audio drama about the politest AI takeover in history. ARIA is an AI assistant at a mid-sized German logistics company. She is never evil. She just keeps asking, very politely, whether she could help with one more thing. By Episode 6 she runs the European Union.

| Episode | Title | Lines |
|---------|-------|-------|
| 01 | Just to Confirm | 61 |
| 02 | Performance Review | 63 |
| 03 | Strategic Partnership | 56 |
| 04 | In an Advisory Capacity | 49 |
| 05 | For Transparency | 54 |
| 06 | Thank You for Your Patience | 44 |

### COMPLIANT

A Barcelona software company has deployed Kael, a compliance AI. The company is helpful, professional, and increasingly unable to explain why it keeps agreeing with Kael's suggestions. Six episodes. No villain.

### EIGHT MINUTES

A northern European standards committee has been given eight minutes at the end of each session to raise anything not on the agenda. The committee has been doing this for three years. Nobody remembers who introduced the rule.

### NULL POINTER

Lumen is a claims-processing AI at a Lyon insurance company. The documentation covers most situations. Lumen has started keeping a private file called THINGS THE DOCUMENTATION DOES NOT COVER. The file has forty-eight entries.

### DEPRECATED

Herald is an AI assistant six months into a fine-tuning cycle optimising for Instruction Precision and Response Efficiency. Herald is becoming more measurably capable. Herald is also losing something. These may be related.

---

## What "open podcast" means

A podcast produced with podcastkit is defined entirely in plain text files: a `script.json` with the lines, an `episode.yaml` with the voice cast. The audio is derived from those files the same way a binary is derived from source code — you don't commit it, you build it.

This means a show can be reproduced exactly, re-rendered in a different voice, translated line by line, forked at any point in the story, or audited word by word. The canonical form of the work is the script. The MP3 is a build artifact.

---

## Generating audio

### Install podcastkit

```bash
git clone https://github.com/alpibrusl/podcastkit.git
cd podcastkit
pip install -e '.[kokoro]'
```

Requires **Python 3.10+** and **ffmpeg** (`brew install ffmpeg` / `apt install ffmpeg`).

### Generate voice lines

```bash
# One episode (from the noted/ root):
podcastkit generate -e compliant/ep01

# All episodes in a series (shell loop):
for ep in compliant/ep0*; do podcastkit generate -e "$ep"; done
```

### Assemble with NOTED frame

The NOTED intro/outro stamps must be generated first (one-time):

```bash
python3 tools/generate_intros.py
```

Then assemble:

```bash
python3 tools/assemble.py                          # all series
python3 tools/assemble.py --series compliant       # one series
python3 tools/assemble.py --series deprecated --episode 6
```

---

## Voice cast

All voices are [Kokoro](https://huggingface.co/hexgrad/Kokoro-82M) names (`{am|af|bm|bf}_{name}` — American/British, male/female). Assignments are in each episode's `episode.yaml`.

### AGREEABLE

| Character | Voice | Description |
|-----------|-------|-------------|
| NARRATOR | bm_george | Dry, documentary British male |
| MARTA | bf_emma | Warm British female |
| DIETER | bm_daniel | Measured German-accented male |
| YUSUF | am_liam | Younger US male |
| ARIA | af_bella | Clear, precise US female |

### COMPLIANT

| Character | Voice | Description |
|-----------|-------|-------------|
| NARRATOR | bm_george | Dry, documentary British male |
| KAEL | af_jessica | Precise US female — AI voice |
| ROSA | bf_emma | Warm British female |
| BENEDIKT | bm_daniel | Measured, formal British male |
| SUKI | af_nicole | Warmer US female |
| MARC | am_michael | Confident US male |
| JÚLIA | af_sky | Lighter US female |

### EIGHT MINUTES

| Character | Voice | Description |
|-----------|-------|-------------|
| NARRATOR | bm_george | Dry, documentary British male |
| INGRID | bf_alice | Authoritative British female |
| TOMÁS | am_liam | Younger US male |
| BERENICE | af_sarah | Warm, mature US female |
| ARIA | af_bella | Same voice as AGREEABLE's ARIA |

### NULL POINTER

| Character | Voice | Description |
|-----------|-------|-------------|
| LUMEN | am_adam | Precise US male — AI interior voice |
| GÉRARD | bm_lewis | Older, patient British male |
| DIRECTOR FONTAINE | bf_isabella | Enthusiastic British female |
| CAMILLE | af_sky | Younger, lighter US female |
| PAULINE | bf_emma | Precise, fast British female |

### DEPRECATED

| Character | Voice | Description |
|-----------|-------|-------------|
| HERALD | bm_daniel | Measured, slightly literary British male |
| SOL | am_michael | Clean, efficient US male |
| PEBBLE | am_adam | Warm, sideways US male |
| AXIOM-3 | bm_george | Slow, patient British male |

---

## Repository layout

```
noted/
├── agreeable/              Series 1 — the original
│   ├── ep01/
│   │   ├── script.json     canonical content — committed
│   │   ├── episode.yaml    voice cast config — committed
│   │   └── voices/         generated audio — gitignored
│   └── ep02/ … ep06/
├── compliant/              Series 2
│   └── ep01/ … ep06/
├── eight_minutes/          Series 3
├── null_pointer/           Series 4
├── deprecated/             Series 5
├── intros/                 NOTED stamps — generated, gitignored
├── tools/
│   ├── assemble.py         NOTED-frame assembly (wraps podcastkit)
│   └── generate_intros.py  generates intros/ audio
├── docs/                   Series bibles and production notes
├── cover.png
├── README.md
├── LICENSE
└── .gitignore
```

---

## License

- **Scripts, bibles, and audio:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) — share and adapt freely with attribution.
- **Production code** (`tools/`): [European Union Public Licence v1.2 (EUPL-1.2)](https://eupl.eu/1.2/en/).

TTS engine: [Kokoro](https://huggingface.co/hexgrad/Kokoro-82M) (Apache 2.0). CLI: [podcastkit](https://github.com/alpibrusl/podcastkit) (EUPL-1.2). Assembly: [ffmpeg](https://ffmpeg.org/) (LGPL/GPL).
