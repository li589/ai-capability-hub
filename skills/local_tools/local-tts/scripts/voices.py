"""Voice registry for local-tts.

Reads ``assets/ref/voices.json`` (preferred) or falls back to scanning
``assets/ref/`` for folders containing ``sound.wav`` + ``text.txt``/``word.txt``.
"""

from __future__ import annotations

import json
from pathlib import Path


def _read_text_file(folder: Path) -> str:
    for name in ("text.txt", "word.txt"):
        path = folder / name
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
    return ""


def _find_audio_file(folder: Path) -> str | None:
    for name in ("sound.wav", "sound.mp3"):
        path = folder / name
        if path.exists():
            return str(path)
    return None


def scan_voices(ref_dir: Path) -> dict:
    """Return {voice_key: {audio, text, folder, keywords, description}} mapping.

    Prefers ``<ref_dir>/voices.json`` if present; otherwise scans subfolders
    of ``<ref_dir>`` for sound+text pairs.
    """
    ref_dir = Path(ref_dir)
    voices: dict = {}
    if not ref_dir.exists():
        return voices

    voices_json = ref_dir / "voices.json"
    if voices_json.exists():
        try:
            config = json.loads(voices_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            config = None
        if isinstance(config, dict):
            for key, cfg in config.items():
                if not isinstance(cfg, dict):
                    continue
                folder = cfg.get("folder", key)
                folder_path = ref_dir / folder
                audio_file = _find_audio_file(folder_path)
                if audio_file is None:
                    continue
                voices[key] = {
                    "audio": audio_file,
                    "text": _read_text_file(folder_path),
                    "folder": folder,
                    "keywords": list(cfg.get("keywords", [key])),
                    "description": cfg.get("description", ""),
                }
            return voices

    for folder in ref_dir.iterdir():
        if not folder.is_dir():
            continue
        audio_file = _find_audio_file(folder)
        if audio_file is None:
            continue
        voices[folder.name] = {
            "audio": audio_file,
            "text": _read_text_file(folder),
            "folder": folder.name,
            "keywords": [folder.name],
            "description": "",
        }
    return voices


def get_voice_info(ref_dir: Path, voice_name: str | None) -> tuple[str, str, str]:
    """Resolve ``voice_name`` to (audio_path, ref_text, resolved_key).

    Resolution order:
      1. Exact key match (case-insensitive).
      2. Keyword match (case-insensitive substring either direction).
      3. Fallback to 'default' key, or the first scanned voice if no default.

    Raises ``ValueError`` if no voices are available.
    """
    voices = scan_voices(Path(ref_dir))
    if not voices:
        raise ValueError(f"No reference voices found in {ref_dir}")

    if voice_name:
        vl = voice_name.lower()
        for name, v in voices.items():
            if vl == name.lower():
                return v["audio"], v["text"], name
        for name, v in voices.items():
            for kw in v.get("keywords", [name]):
                kwl = kw.lower()
                if kwl == vl or kwl in vl or vl in kwl:
                    return v["audio"], v["text"], name

    if "default" in voices:
        v = voices["default"]
        return v["audio"], v["text"], "default"

    first = next(iter(voices))
    v = voices[first]
    return v["audio"], v["text"], first
