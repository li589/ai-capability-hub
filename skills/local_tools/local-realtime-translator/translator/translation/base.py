"""Base interface for translation models."""

from abc import ABC, abstractmethod
from typing import Generator


class BaseTranslator(ABC):
    """Translation model interface."""

    @abstractmethod
    def load(self, src_lang: str, tgt_lang: str):
        """Load model for a language pair."""
        ...

    @abstractmethod
    def translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        """Translate text (blocking, returns full result)."""
        ...

    def translate_stream(self, text: str, src_lang: str, tgt_lang: str
                         ) -> Generator[str, None, None]:
        """Optional: yield progressively cleaner partial translations as they
        are generated.

        The default implementation yields the full result from ``translate()``
        in a single shot. Subclasses that support token-level streaming should
        override this to yield partial text as tokens arrive. The **last**
        yielded value is the final, fully-cleaned translation.

        Yields
            Partial translation strings. Each yield replaces the previous one
            (the caller should update the display on each yield). The final
            yield is the authoritative result.
        """
        yield self.translate(text, src_lang, tgt_lang)
