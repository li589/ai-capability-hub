"""Text utilities for ASR post-processing and output filtering."""

import re

# Characters that carry no translatable meaning on their own: ASCII and CJK
# punctuation, whitespace. A "sentence" made only of these is noise.
_PUNCT = r"""!"#$%&'()*+,\-./:;<=>?@\[\]\\^_`{|}~""" \
    + "。，、；：？！…—·《》「」『』（）【】〔〕“”‘’～"
_PUNCT_ONLY_RE = re.compile(rf"^[\s{re.escape(_PUNCT)}]*$")

# Count of "real" content characters (letters/digits/CJK), ignoring punctuation
# and whitespace.
_CONTENT_RE = re.compile(r"[^\s" + re.escape(_PUNCT) + r"]")

# Minimum content characters for a sentence to be worth translating. One stray
# recognized character from background noise is dropped; two or more are kept.
MIN_CONTENT_CHARS = 2


def content_char_count(text: str) -> int:
    """Number of non-whitespace, non-punctuation characters in ``text``."""
    if not text:
        return 0
    return len(_CONTENT_RE.findall(text))


# A single character repeated this many times or more is treated as an ASR
# stutter/hallucination (e.g. "啊啊啊啊啊") and collapsed. Legitimate doubling
# ("谢谢", "慢慢", "好好") and tripling ("哈哈哈") stay below this threshold.
_MAX_CHAR_RUN = 4

# Same threshold for a repeated multi-char phrase ("我们我们我们" -> "我们").
_MAX_PHRASE_REPEAT = 3

_WS_RE = re.compile(r"\s+")
# A run of one identical character, length >= _MAX_CHAR_RUN.
_CHAR_RUN_RE = re.compile(r"(.)\1{" + str(_MAX_CHAR_RUN - 1) + r",}")
# A short phrase (2-6 chars) immediately repeated _MAX_PHRASE_REPEAT+ times.
_PHRASE_RUN_RE = re.compile(r"(.{2,6}?)\1{" + str(_MAX_PHRASE_REPEAT - 1) + r",}")


def clean_asr_text(text: str) -> str:
    """Conservatively clean ASR output before translation.

    ASR models emit stutters and hallucinated repetitions, especially on noisy
    or clipped audio. This normalizes the obvious cases without touching
    plausibly-legitimate content:

    - trims surrounding whitespace and collapses internal whitespace runs;
    - collapses a single character repeated >= 4 times to two occurrences
      (legitimate doublings/triplings like "谢谢"/"哈哈哈" are left alone);
    - collapses a short phrase repeated >= 3 times to a single occurrence
      ("我们我们我们" -> "我们").

    Intentionally conservative: it would rather leave a borderline repetition
    in than corrupt a real sentence.
    """
    if not text:
        return text

    text = text.strip()
    if not text:
        return text

    text = _WS_RE.sub(" ", text)
    # Collapse an over-long single-char run down to two of that character.
    text = _CHAR_RUN_RE.sub(lambda m: m.group(1) * 2, text)
    # Collapse an over-repeated short phrase down to one occurrence.
    text = _PHRASE_RUN_RE.sub(lambda m: m.group(1), text)
    return text.strip()


def strip_asr_prefix(text: str) -> str:
    """Strip Qwen3-ASR's metadata prefix from a streaming partial decode.

    Qwen3-ASR emits ``language Chinese<asr_text>real text``: a metadata header
    naming the detected language, an ``<asr_text>`` open tag, then the actual
    transcription. The metadata tokens are produced first, so a streaming
    decode leaks ``language Chinese<asr_text>`` into the UI before any real
    text arrives. ``<asr_text>`` is plain text (not a special token), so
    ``skip_special_tokens`` does not remove it.

    Mirror the final ``parse_asr_output`` here:

    - once ``<asr_text>`` appears, keep only what follows it;
    - while only the ``language …`` header has been emitted, return ``""``
      (real text has not started yet).

    Anything not matching this shape is returned unchanged, preserving the
    "no tag => pure text" fallback (e.g. a forced-language run that outputs
    bare transcription).
    """
    if not text:
        return text
    if "<asr_text>" in text:
        return text.split("<asr_text>", 1)[1]
    if text.lstrip().lower().startswith("language"):
        return ""
    return text


def is_meaningful(text: str, min_chars: int = MIN_CONTENT_CHARS) -> bool:
    """True if ``text`` has enough real content to be worth translating.

    Filters out empty strings, pure whitespace, punctuation-only output, and
    ultra-short fragments (a single character) that ASR commonly emits from
    background noise. Without this, such noise triggers a wasted translation
    and an empty/garbage TTS clip on disk for every spurious VAD segment.
    """
    if not text or not text.strip():
        return False
    if _PUNCT_ONLY_RE.match(text):
        return False
    return content_char_count(text) >= min_chars
