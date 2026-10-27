#!/usr/bin/env python3
"""Render a voiceover with Chatterbox TTS.

A script is split into beats on blank lines. Each beat is generated on its own,
then joined with silence. A line like `[pause 1.2]` inserts that many seconds of
silence in place of the default gap.

Examples:
  vo.py "You built it. Now brag." -o out.wav
  vo.py --file script.txt --model nano --ref voice.wav -o vo.wav
  vo.py --file hindi.txt --model multilingual --lang hi -o vo_hi.wav
"""

import argparse
import re
import sys
from pathlib import Path

PAUSE_RE = re.compile(r"^\[pause\s+([0-9]*\.?[0-9]+)\]$", re.IGNORECASE)


def parse_beats(text):
    """Return a list of ("speak", str) and ("pause", seconds) items."""
    items = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        speech = []
        for line in lines:
            m = PAUSE_RE.match(line)
            if m:
                if speech:
                    items.append(("speak", " ".join(speech)))
                    speech = []
                items.append(("pause", float(m.group(1))))
            else:
                speech.append(line)
        if speech:
            items.append(("speak", " ".join(speech)))
    return items


def pick_device(requested):
    import torch

    if requested != "auto":
        return requested
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load_model(name, device, lang):
    if name in ("turbo", "nano"):
        from chatterbox.tts_turbo import ChatterboxTurboTTS

        return ChatterboxTurboTTS.from_pretrained(device=device, nano=name == "nano")
    if name == "standard":
        from chatterbox.tts import ChatterboxTTS

        return ChatterboxTTS.from_pretrained(device=device)
    if name == "multilingual":
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS

        if not lang:
            sys.exit("--lang is required for the multilingual model (e.g. en, hi, fr)")
        return ChatterboxMultilingualTTS.from_pretrained(device=device, t3_model="v3")
    sys.exit(f"unknown model: {name}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("text", nargs="?", help="Text to speak. Omit when using --file.")
    p.add_argument("--file", "-f", type=Path, help="Script file. Blank lines separate beats.")
    p.add_argument("--out", "-o", type=Path, default=Path("vo.wav"), help="Output .wav path")
    p.add_argument("--model", "-m", default="turbo", choices=["turbo", "nano", "standard", "multilingual"])
    p.add_argument("--ref", type=Path, help="Reference clip to clone (wav, over 5 seconds, ~10s ideal)")
    p.add_argument("--lang", help="Language id for multilingual (en, hi, ar, fr, ...)")
    p.add_argument("--exaggeration", type=float, default=0.5, help="Standard/multilingual only. 0.7+ for drama")
    p.add_argument("--cfg", type=float, default=0.5, help="Standard/multilingual only. ~0.3 slows pacing")
    p.add_argument("--temperature", type=float, default=0.8)
    p.add_argument("--gap", type=float, default=0.45, help="Seconds of silence between beats")
    p.add_argument("--device", default="auto", help="auto, cuda, mps or cpu")
    p.add_argument("--stems", action="store_true", help="Also write each beat as its own wav")
    args = p.parse_args()

    if args.file:
        text = args.file.read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        p.error("give text or --file")
    if args.ref and not args.ref.exists():
        sys.exit(f"reference clip not found: {args.ref}")

    items = parse_beats(text)
    if not any(kind == "speak" for kind, _ in items):
        sys.exit("nothing to speak")

    import torch
    import torchaudio as ta

    device = pick_device(args.device)
    print(f"model={args.model} device={device} beats={sum(k == 'speak' for k, _ in items)}", file=sys.stderr)
    model = load_model(args.model, device, args.lang)
    sr = model.sr

    kwargs = {"temperature": args.temperature}
    if args.model in ("standard", "multilingual"):
        kwargs.update(exaggeration=args.exaggeration, cfg_weight=args.cfg)
    if args.model == "multilingual":
        kwargs["language_id"] = args.lang

    args.out.parent.mkdir(parents=True, exist_ok=True)
    pieces = []
    prepared = False
    beat = 0
    for i, (kind, value) in enumerate(items):
        if kind == "pause":
            pieces.append(torch.zeros(1, int(sr * value)))
            continue
        beat += 1
        print(f"[{beat}] {value}", file=sys.stderr)
        # Condition on the reference clip once, then reuse it for every beat.
        ref = str(args.ref) if args.ref and not prepared else None
        wav = model.generate(value, audio_prompt_path=ref, **kwargs).cpu()
        prepared = prepared or ref is not None
        if args.stems:
            ta.save(str(args.out.with_name(f"{args.out.stem}_{beat:02d}.wav")), wav, sr)
        pieces.append(wav)
        nxt = items[i + 1][0] if i + 1 < len(items) else None
        if nxt == "speak":
            pieces.append(torch.zeros(1, int(sr * args.gap)))

    ta.save(str(args.out), torch.cat(pieces, dim=1), sr)
    print(args.out)


if __name__ == "__main__":
    main()
