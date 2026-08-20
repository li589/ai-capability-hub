"""
Pipeline constants - imported as: import src.config as config
"""

# ============================================================
# Shared Infrastructure
# ============================================================
GPU_TYPE = "L4"
PYTHON_VERSION = "3.11"

# Shared Volume names — both denoise and isolate use the same volumes
# Isolation is provided by slug (different directories under the same volume)
VOLUME_DATA_NAME = "speech2srt-data"
VOLUME_MODELS_NAME = "speech2srt-models"

# Shared Volume mount points
MOUNT_DATA = "/mnt/data"
MOUNT_MODELS = "/mnt/models"

# Pipeline directory names (same for both pipelines)
DIR_UPLOAD = "upload"  # under /mnt/data/<slug>/
DIR_OUTPUT = "output"  # under /mnt/data/<slug>/

# Intermediate files written to container SSD (not volume)
# Separate prefixes so denoise/isolate/transcribe don't conflict during parallel runs
TMP_PREFIX_DENOISE = "/tmp/speech2srt-denoise"
TMP_PREFIX_ISOLATE = "/tmp/speech2srt-isolate"
TMP_PREFIX_CHAINED = "/tmp/speech2srt-isolate-denoise"  # chained pipeline
TMP_PREFIX_TRANSCRIBE = "/tmp/speech2srt-transcribe"

# ============================================================
# App Name
# ============================================================
APP_NAME = "speech2srt.com"

# ============================================================
# Output Suffixes
# ============================================================
ISOLATED_SUFFIX = "_isolated.wav"  # isolate+denoise chained pipeline output
TRANSCRIPTION_SUFFIX = "_transcription"  # transcribe pipeline output

# ============================================================
# Audio Processing Config
# ============================================================
AUDIO_SAMPLE_RATE = 48000  # Hz
AUDIO_CHANNELS = 1  # mono
AUDIO_FORMAT = "WAV"
AUDIO_SUBTYPE = "PCM_24"
AUDIO_STEREO_NDIM = 2  # shape dimension that indicates (channels, samples) layout

# ============================================================
# File Extension Config
# ============================================================
FLAC_EXTENSION = ".flac"

# ============================================================
# Timeout Config (seconds)
# ============================================================
TIMEOUT_DENOISE = 1800  # Single stage (GPU)
TIMEOUT_CHAINED = 3600  # Chained isolate + denoise (GPU, 60min)
TIMEOUT_TRANSCRIBE = 3600  # Transcribe (larger model, longer audio)
FFMPEG_TIMEOUT = 300  # per-file conversion
FFPROBE_TIMEOUT = 30  # per-file probe

# ============================================================
# Transcribe Config
# ============================================================
TRANSCRIBE_MODEL_NAME = "large-v3"  # Transcribe model size
