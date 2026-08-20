"""Speaker identification - RESERVED for future implementation.

Interface defined here so live_pipeline can be wired up without code changes
when CAM++ is integrated in a later iteration.
"""

import numpy as np
from typing import Optional

from translator.messages import SentenceAudio


class SpeakerIdentifier:
    """Speaker ID interface. Current implementation is a no-op placeholder."""

    def __init__(self):
        self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def load(self):
        """Load speaker model. Not implemented yet."""
        raise NotImplementedError("Speaker ID not implemented in this version.")

    def identify(self, sentence: SentenceAudio) -> int:
        """Identify speaker. Returns -1 (unknown) in placeholder mode."""
        return -1

    def reset(self):
        """Reset speaker state."""
        pass
