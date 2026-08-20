"""Audio capture from microphone using sounddevice (WASAPI on Windows)."""

import time
import numpy as np
import sounddevice as sd

import config


class AudioCapture:
    """Captures audio from the default microphone via sounddevice callback."""

    def __init__(self):
        self._stream = None
        self._start_time_ms = 0
        self._samples_captured = 0
        self._listeners = []

    def add_listener(self, callback):
        """Register callback(samples: np.ndarray, timestamp_ms: int)."""
        self._listeners.append(callback)

    def _callback(self, indata, frames, time_info, status):
        samples = indata[:, 0].copy()
        ts = self._start_time_ms + int(self._samples_captured * 1000 / config.SAMPLE_RATE)
        self._samples_captured += len(samples)
        for cb in self._listeners:
            cb(samples, ts)

    def start(self):
        self._start_time_ms = int(time.time() * 1000)
        self._samples_captured = 0
        self._stream = sd.InputStream(
            samplerate=config.SAMPLE_RATE,
            channels=config.CHANNELS,
            dtype=config.DTYPE,
            blocksize=config.BLOCK_SIZE,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self):
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
