---
name: chatterbox-vo
description: Render voiceover audio locally with Chatterbox TTS (Resemble AI, open source). Use when a motion piece, launch video or ad needs a VO track, a scratch read, a cloned voice from a reference clip, or a read in Hindi, Arabic or another of 23 languages. Triggers on "voiceover", "VO", "narration", "read this line", "text to speech", "clone this voice", "/chatterbox-vo".
---

# Chatterbox VO

Turns a VO script into a `.wav`. Runs on this machine, no API key, no credits.

Source is vendored at `chatterbox/` (upstream `resemble-ai/chatterbox` at `5de7a54`). The renderer is `scripts/vo.py` next to this file.

## Setup

Check first, install only if missing:

```bash
python -c "import chatterbox" 2>/dev/null && echo ready
```

If not ready, use Python 3.11 in its own environment:

```bash
python3.11 -m venv ~/.venvs/chatterbox
source ~/.venvs/chatterbox/bin/activate
pip install -e chatterbox
```

Torch 2.6.0 is pinned. Weights download from Hugging Face on first run of each model (about 1 to 3 GB), then cache.

## Pick a model

| Model | Flag | Use for |
|---|---|---|
| Turbo, 350M, English | `--model turbo` (default) | Best English read. Supports event tags. Needs a GPU to be quick. |
| Nano, 110M, English | `--model nano` | CPU machines, fast drafts. Same tags as Turbo. |
| Original, 500M, English | `--model standard` | When you need `--exaggeration` and `--cfg` control for a dramatic read. |
| Multilingual V3, 500M | `--model multilingual --lang hi` | Hindi, Arabic, French and 20 more. Language ids: ar da de el en es fi fr he hi it ja ko ms nl no pl pt ru sv sw tr zh. |

No GPU here? Use `nano` for English. Multilingual on CPU works, just slowly.

## Render

```bash
SKILL=.claude/skills/chatterbox-vo
python $SKILL/scripts/vo.py --file vo/script.txt --model turbo -o vo/vo.wav
python $SKILL/scripts/vo.py "You built it. Now brag." --model nano -o vo/line.wav
python $SKILL/scripts/vo.py --file vo/hi.txt --model multilingual --lang hi --ref vo/voice.wav -o vo/vo_hi.wav
```

Options:

- `--ref clip.wav`: clone a voice. Clip must be over 5 seconds, about 10 is ideal. Clean, dry, one speaker. Without it, the model's built-in voice is used.
- `--gap 0.45`: silence between beats, in seconds.
- `--stems`: also write each beat as `name_01.wav`, `name_02.wav` for cutting to picture.
- `--exaggeration`, `--cfg`: standard and multilingual only. Turbo and Nano ignore them.
- `--device cuda|mps|cpu`: defaults to the best available.

## Writing the script file

A VO is spoken, not read. Shape the file for performance.

- **Blank line = new beat.** Each beat is generated on its own, so keep a beat to one breath. Short beats give cleaner, more controllable reads.
- **`[pause 1.2]` on its own line** = that many seconds of silence. Use it where a line needs to land.
- **Punctuation drives delivery.** Full stop for a drop. Comma for a lift and carry. Question mark for a rise. Ellipses read as hesitation.
- **Event tags, Turbo and Nano only:** `[laugh]` `[chuckle]` `[sigh]` `[gasp]` `[cough]` `[clear throat]` `[sniff]` `[groan]` `[shush]`. Put them inline: `Took us a year [sigh] and it was worth it.`
- **Spell for the ear.** Write numbers, acronyms and brand names the way they should sound: "twenty twenty-six", "A I", "Mammoth A I".

Example `script.txt`:

```
You built it.

[pause 0.6]

Now brag.

One command. Music, motion, share copy.

Done before your coffee cools.
```

## Tuning a read (standard and multilingual)

- Defaults (`--exaggeration 0.5 --cfg 0.5`) suit most lines.
- Dramatic: `--exaggeration 0.7 --cfg 0.3`. Higher exaggeration speeds speech up, lower cfg slows it back down.
- Fast-talking reference voice: drop `--cfg` to about 0.3.
- Reference clip in a different language from `--lang`: set `--cfg 0` so the accent doesn't bleed across.

## Deliver

- Output is mono WAV at the model's native rate (`model.sr`, 24 kHz).
- Every file carries Resemble's inaudible Perth watermark. Tell the client if that matters for the delivery.
- Listen back before handing off. When one line misfires, render just that line as text and swap it in. Use `--stems` so every beat is already its own file. Sampling varies run to run, so a second take often fixes it.
- Only clone a voice you have the rights to.
