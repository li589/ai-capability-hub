"""Lock-free-style ring buffer for audio samples."""

import numpy as np
import threading


class RingBuffer:
    """Fixed-capacity ring buffer for float32 audio samples."""

    def __init__(self, capacity_samples: int):
        self._buf = np.zeros(capacity_samples, dtype=np.float32)
        self._capacity = capacity_samples
        self._write_pos = 0
        self._read_pos = 0
        self._lock = threading.Lock()

    @property
    def available(self) -> int:
        with self._lock:
            return (self._write_pos - self._read_pos) % self._capacity

    def write(self, data: np.ndarray) -> int:
        n = len(data)
        if n == 0:
            return 0
        if n >= self._capacity:
            data = data[-self._capacity + 1:]
            n = len(data)

        with self._lock:
            wp = self._write_pos
            end = wp + n
            if end <= self._capacity:
                self._buf[wp:end] = data
            else:
                first = self._capacity - wp
                self._buf[wp:] = data[:first]
                self._buf[:n - first] = data[first:]
            self._write_pos = end % self._capacity
        return n

    def read(self, n_samples: int) -> np.ndarray:
        with self._lock:
            avail = (self._write_pos - self._read_pos) % self._capacity
            n = min(n_samples, avail)
            if n == 0:
                return np.array([], dtype=np.float32)
            rp = self._read_pos
            end = rp + n
            if end <= self._capacity:
                out = self._buf[rp:end].copy()
            else:
                first = self._capacity - rp
                out = np.concatenate([self._buf[rp:], self._buf[:n - first]])
            self._read_pos = end % self._capacity
        return out

    def clear(self):
        with self._lock:
            self._read_pos = self._write_pos
