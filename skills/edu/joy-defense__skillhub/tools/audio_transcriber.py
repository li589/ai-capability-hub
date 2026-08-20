#!/usr/bin/env python3
"""
audio_transcriber.py
CLI wrapper around OpenAI Whisper (local, open-source) for transcription.

- Usage: python audio_transcriber.py --input <audio_file> --output <result.json> [--model <model>]
- Models: tiny, base, small, medium, large (default: base)
- No paid APIs; relies on Whisper model downloaded on first run.
- Outputs JSON with: file, duration_seconds, language, text, segments
"""

import argparse
import json
import os


def transcribe_audio(audio_path: str, model_name: str = "base") -> dict:
    # Lazy import to avoid failing if user only wants help text
    import whisper

    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path)
    # Normalize structure
    duration = result.get("duration")
    if duration is None:
        # Fallback: infer from segments
        segs = result.get("segments", [])
        duration = max((s.get("end", 0) for s in segs), default=0)
    language = result.get("language")
    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": seg.get("start"),
            "end": seg.get("end"),
            "text": seg.get("text"),
            "confidence": seg.get("confidence"),
        })
    return {
        "file": os.path.abspath(audio_path),
        "duration_seconds": duration,
        "language": language,
        "text": result.get("text"),
        "segments": segments,
    }


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio using Whisper (local).")
    parser.add_argument("--input", required=True, help="Path to audio file (.mp3, .wav, .m4a, .mp4, .avi)")
    parser.add_argument("--output", required=True, help="Path to output JSON file")
    parser.add_argument("--model", default="base", help="Whisper model name: tiny, base, small, medium, large")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        raise SystemExit(f"Input audio not found: {args.input}")

    result = transcribe_audio(args.input, args.model)
    # Write output JSON
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Also print a small summary to stdout for convenience
    print(json.dumps({"file": result["file"], "duration_seconds": result["duration_seconds"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
