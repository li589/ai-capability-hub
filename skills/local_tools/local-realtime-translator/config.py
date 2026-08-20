"""Global configuration for realtime-translator."""

# Audio capture
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "float32"
BLOCK_MS = 32
BLOCK_SIZE = 512  # 32ms @ 16kHz

# VAD (FunASR FSMN-VAD with endpoint detection)
VAD_MIN_SPEECH_MS = 250
FSMN_VAD_MODEL = "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch"
FSMN_VAD_CHUNK_MS = 200  # chunk size for streaming VAD (ms)
# Silence (ms) the VAD must observe before it declares a sentence endpoint.
# This is an ACOUSTIC, not semantic, boundary: a sentence ends once this much
# continuous silence is seen, regardless of whether the utterance is
# semantically complete. Lower values segment sooner (lower latency) at the
# risk of splitting on mid-sentence pauses; higher values tolerate pauses but
# delay the final transcription. Set to 800ms: a pause is only recognized after
# 800ms of continuous silence.
FSMN_VAD_MAX_END_SILENCE_MS = 800  # max silence before endpoint (ms)
# Rolling pre-buffer kept before speech is confirmed, so the sentence head can
# be recovered once FSMN-VAD finally fires. FSMN-VAD's detection latency from
# true onset to the start event can exceed 1s, so this must be generous (the
# old fixed 320ms clipped the first syllable). On speech-start the buffer is
# sliced back to the reported start_ms minus VAD_ONSET_MARGIN_MS (a cushion for
# the VAD under-reporting the onset).
VAD_PRE_BUFFER_MS = 2000   # rolling pre-speech audio retained (ms)
VAD_ONSET_MARGIN_MS = 200  # extra lead-in kept before reported start_ms (ms)

# Paraformer streaming ASR
PARAFORMER_ONLINE_MODEL = "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online"
PARAFORMER_OFFLINE_MODEL = "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
PARAFORMER_CHUNK_MS = 600
PARAFORMER_CHUNK_SIZE = int(SAMPLE_RATE * PARAFORMER_CHUNK_MS / 1000)  # 9600
# Streaming chunk config: [left_lookback, center, right_lookahead] in 60ms units.
# [0, 10, 5] == 600ms center chunk with 300ms lookahead.
PARAFORMER_CHUNK_LOOK = [0, 10, 5]
# History the streaming encoder/decoder may attend to across chunks. FunASR
# defaults BOTH to 0 (no cross-chunk context), which makes each 600ms chunk be
# decoded in isolation and inflates streaming WER (and produces tail
# hallucinations). The official online-Paraformer example uses 4 / 1, which on
# the bundled asr_example.wav cuts streaming CER from ~0.16 to ~0.00.
PARAFORMER_ENCODER_LOOK_BACK = 4
PARAFORMER_DECODER_LOOK_BACK = 1

# Punctuation restoration (FunASR ct-punc) for the Paraformer-Offline fallback.
# Paraformer emits raw, unpunctuated text; on benchmarks its CER gap vs Qwen3
# was almost entirely punctuation, not wrong characters. When Qwen3 is
# unavailable we run the offline result through ct-punc so the fallback output
# reads like a finished sentence (commas / periods / question marks). Qwen3
# already punctuates, so its path is left untouched.
#   - The small zh-cn model (~290MB) is enough for Chinese punctuation and is
#     fast on CPU; the large cn-en model (~1GB) is overkill here.
#   - Loaded lazily on first use, so it costs nothing unless the fallback path
#     actually runs. Set PUNC_ENABLED=False to disable entirely.
PUNC_ENABLED = True
PUNC_MODEL = "iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch"

# Qwen3-ASR (iGPU via OpenVINO)
QWEN_MODEL_ID = "snake7gun/Qwen3-ASR-0.6B-fp16-ov"
QWEN_DEVICE = "GPU"
# Optional explicit location of the Qwen3-ASR engine dir (the folder holding
# asr_engine.py, with models/Qwen3-ASR-0.6B-fp16-ov/ and state.json beside it).
# Set this to skip the legacy "<drive>:\<username>_openvino\asr" drive scan and
# point straight at the install. Reads the QWEN_ASR_DIR env var first, then this
# constant; when both are empty, accurate.py falls back to scanning drives A:-Z:.
# Leaving it unset is fine — Qwen3-ASR is optional and the pipeline degrades to
# Paraformer Offline (CPU) when no engine is found.
import os as _os
QWEN_ASR_DIR = _os.environ.get("QWEN_ASR_DIR", "")

# ── Local model root ─────────────────────────────────────────────────────
# Every model the pipeline uses is pre-downloaded by scripts/ensure_models.py
# (atomic snapshot_download via the shared model_download helper) into a
# per-model directory under this root. Consumers load straight from here so the
# runtime never re-hits the network on a validated install.
MODELS_ROOT = _os.path.join(
    _os.environ.get("USERPROFILE", _os.path.expanduser("~")), ".openvino", "models"
)


def local_model_dir(model_id: str) -> str:
    """Return the local directory ``model_id`` is downloaded into under MODELS_ROOT.

    The directory name is the last path segment of the model id, matching the
    ``dir_name`` scripts/ensure_models.py downloads each model into (and the
    ``dir_name`` entries in info.json). Works for both the ModelScope download
    id and the bare HuggingFace id a consumer holds, because they share that
    last segment for every model the pipeline uses.
    """
    return _os.path.join(MODELS_ROOT, model_id.split("/")[-1])

# Speaker ID (CAM++) - reserved for future use
SPEAKER_MODEL = "iic/speech_campplus_sv_zh-cn_16k-common"
SPEAKER_ENABLED = False

# Whisper (English ASR) - reserved for future use
WHISPER_MODEL = "base"
WHISPER_DEVICE = "CPU"
WHISPER_ENABLED = False

# Translation (Hunyuan-1.8B-Instruct on iGPU via OpenVINO)
HUNYUAN_MODEL_ID = "snake7gun/Hunyuan-1.8B-Instruct-ov-int4"
HUNYUAN_DEVICE = "GPU"
# Safety fuse for streaming translation. generate() runs in a background thread
# feeding a TextIteratorStreamer; the stop signal is only emitted when generate()
# finishes normally. If generate() raises or the iGPU wedges, the streamer queue
# would otherwise block forever. This timeout (seconds) bounds each queue wait so
# the consumer can break out and fall back to Opus-MT. Set generously — it is a
# dead-man's switch, NOT a latency control; a normal sentence finishes well under
# it. Must exceed the worst-case time to generate one full translation.
HUNYUAN_STREAM_TIMEOUT_S = 30.0

# Fallback translation (Opus-MT)
# These ids exist on BOTH HuggingFace and ModelScope under the same namespace
# (verified). We download/load them from ModelScope by default (stable in CN,
# no HuggingFace dependency); see translator/translation/opus_mt.py.
TRANSLATION_MODELS = {
    ("zh", "en"): "Helsinki-NLP/opus-mt-zh-en",
    ("en", "zh"): "Helsinki-NLP/opus-mt-en-zh",
}

# ── HuggingFace access / mirror ──────────────────────────────────────────
# Some components pull models straight from HuggingFace through third-party
# libraries we don't control the source of (MeloTTS' internal hf_hub_download
# for its checkpoint/config, and bert-base-uncased for English prosody). When
# HuggingFace is slow or blocked (e.g. from CN), those downloads stall the whole
# first-run.
#
# Two-tier strategy:
#   1) For models we DO control loading of (Opus-MT), prefer ModelScope mirrors
#      via snapshot_download — see opus_mt.py / download_models.py.
#   2) For the rest, point huggingface_hub at a mirror via the HF_ENDPOINT env
#      var. hf-mirror.com is a well-established CN mirror. This MUST be set
#      before huggingface_hub is imported, so entrypoints call
#      apply_hf_mirror() at the very top (see main.py / scripts/server.py).
# Set HF_MIRROR_ENABLED=False to use HuggingFace directly.
HF_MIRROR_ENABLED = True
HF_MIRROR_ENDPOINT = "https://hf-mirror.com"

# ModelScope ids for the HuggingFace-origin models, used to fetch them from
# ModelScope instead of HF. Verified to be complete mirrors of the same models.
#
# The bert-* and MeloTTS-* entries are consumed by melo_hf_bridge.py, which
# routes MeloTTS' hardcoded HuggingFace loads through ModelScope. MeloTTS is the
# ONLY component left that pulls from HF; on networks that reach ModelScope but
# block hf-mirror.com (common in CN corporate environments) this is what kept
# first-run from completing — the bridge fixes it.
MODELSCOPE_MIRRORS = {
    "Helsinki-NLP/opus-mt-zh-en": "Helsinki-NLP/opus-mt-zh-en",
    "Helsinki-NLP/opus-mt-en-zh": "Helsinki-NLP/opus-mt-en-zh",
    # English prosody BERT (melo/text/english.py + english_bert.py).
    "bert-base-uncased": "AI-ModelScope/bert-base-uncased",
    # Chinese (ZH_MIX_EN) prosody BERT (melo/text/chinese_mix.py).
    "bert-base-multilingual-uncased": "google-bert/bert-base-multilingual-uncased",
    # MeloTTS voice config + checkpoint, fetched in melo's download_utils.
    "myshell-ai/MeloTTS-English": "myshell-ai/MeloTTS-English",
    "myshell-ai/MeloTTS-Chinese": "myshell-ai/MeloTTS-Chinese",
}

# MeloTTS language code -> its HuggingFace repo id (melo's LANG_TO_HF_REPO_ID).
# Used by melo_hf_bridge to resolve the voice config/checkpoint from ModelScope
# and hand explicit local paths to melo.api.TTS (bypassing its HF download).
MELOTTS_HF_REPOS = {
    "EN": "myshell-ai/MeloTTS-English",
    "ZH": "myshell-ai/MeloTTS-Chinese",
}


def apply_hf_mirror():
    """Point huggingface_hub at the CN mirror, if enabled.

    Must run BEFORE huggingface_hub / transformers / melo are imported, since
    HF reads HF_ENDPOINT at import time. Safe to call multiple times; only sets
    the var when not already provided by the environment.
    """
    import os
    if HF_MIRROR_ENABLED and not os.environ.get("HF_ENDPOINT"):
        os.environ["HF_ENDPOINT"] = HF_MIRROR_ENDPOINT


# NLTK g2p data (averaged_perceptron_tagger + cmudict) is bundled with the skill
# under src/nltk_data/ so English G2P never depends on NLTK's GitHub download
# (raw.githubusercontent.com), which is blocked on CN/corporate networks AND has
# no timeout — nltk.download() would otherwise hang first-run forever.
# (_os is imported at module top, near QWEN_ASR_DIR.)
_NLTK_DATA_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "nltk_data")


def ensure_bundled_nltk_data():
    """Register the bundled NLTK data dir on nltk.data.path (offline, no network).

    Must run BEFORE g2p_en / melo are imported: g2p_en calls nltk.download() at
    MODULE-import time if it can't already find the tagger/cmudict locally.
    Prepends so the bundled copy wins. Safe to call repeatedly. No-op if nltk
    isn't installed or the bundled dir is absent (degrades to NLTK's own lookup).
    """
    if not _os.path.isdir(_NLTK_DATA_DIR):
        return
    # Belt-and-suspenders: NLTK also honours the NLTK_DATA env var at import.
    existing = _os.environ.get("NLTK_DATA", "")
    if _NLTK_DATA_DIR not in existing.split(_os.pathsep):
        _os.environ["NLTK_DATA"] = (
            _NLTK_DATA_DIR + (_os.pathsep + existing if existing else "")
        )
    try:
        import nltk.data
        if _NLTK_DATA_DIR not in nltk.data.path:
            nltk.data.path.insert(0, _NLTK_DATA_DIR)
    except Exception:
        pass

# TTS (MeloTTS)
TTS_SAMPLE_RATE = 44100
TTS_SPEED = 1.0
# Rolling cap on the per-sentence WAV files written to output/. Each finished
# sentence writes one sentence_XXXX.wav and they were previously kept forever;
# a long-running session (the web UI is a persistent service) would slowly fill
# the disk (~1 hr ≈ 500 files ≈ 300MB). After writing a new WAV the TTS loop
# prunes the oldest files (by modification time) so at most this many remain.
# Already-played files in the web UI are fetched over HTTP and not needed again,
# so deleting old ones affects no live state. Set <= 0 to disable pruning.
TTS_OUTPUT_KEEP = 100

# WebSocket server
WS_HOST = "127.0.0.1"
WS_PORT = 8765
