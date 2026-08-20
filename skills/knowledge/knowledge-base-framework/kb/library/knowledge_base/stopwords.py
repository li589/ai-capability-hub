"""
Stopword Handling for Knowledge Base
====================================

Phase 3: Extended German stopwords via NLTK.
Expands from ~38 to 300+ stopwords for better keyword extraction.

Source: KB_Erweiterungs_Plan.md (Phase 3)
"""

import logging
from typing import Optional, Set, List

logger = logging.getLogger(__name__)


class StopwordHandler:
    """
    German stopword handler with NLTK integration.
    
    Stopwords are common words filtered out during keyword extraction.
    Extended German stopword list from NLTK:
    - German corpora stopwords: ~300 words
    - Custom additions for medical/technical context
    
    Usage:
        handler = StopwordHandler()
        keywords = [w for w in text.split() if not handler.is_stopword(w)]
    """
    
    # Minimal German stopwords (fallback if NLTK unavailable)
    MINIMAL_GERMAN_STOPWORDS: Set[str] = {
        # Articles
        "der", "die", "das", "den", "dem", "des", "ein", "eine", "einer", "einem", "einen", "eines",
        # Pronouns
        "ich", "du", "er", "sie", "es", "wir", "ihr", "mich", "dich", "sich", "uns", "euch",
        "mein", "dein", "sein", "ihr", "unser", "euer",
        "dieser", "diese", "dieses", "jener", "jene", "jenes",
        "wer", "was", "wo", "wie", "wann", "warum", "welche", "welcher", "welches",
        # Prepositions
        "an", "auf", "aus", "bei", "bis", "durch", "für", "gegen", "in", "mit", "nach", "ohne",
        "um", "unter", "von", "vor", "zu", "zur", "zum", "über",
        # Conjunctions
        "und", "oder", "aber", "auch", "als", "wie", "wenn", "weil", "dass", "damit", "ob",
        # Verbs (common)
        "ist", "sind", "war", "waren", "hat", "haben", "hatte", "hatten", "wird", "werden",
        "kann", "kannst", "können", "konnte", "muss", "musst", "müssen", "musste",
        "soll", "sollst", "sollen", "sollte", "wollte", "will", "willst", "wollen",
        "mag", "magst", "mögen", "mochte",
        # Adverbs
        "nicht", "kein", "keine", "keiner", "keinem", "keinen",
        "ja", "nein", "doch", "vielleicht", "wahrscheinlich", "ziemlich", "sehr", "mehr",
        "hier", "da", "dort", "heute", "jetzt", "immer", "noch", "schon", "bald", "wieder",
        "so", "nur", "denn", "dann", "als", "bis", "ob", "obwohl",
        # Other common
        "amp", "und", "oder", "aber", "im", "am", "beim", "vom", "zum", "zur", "aus",
        "nach", "vor", "über", "unter", "mit", "bei", "von", "durch", "ohne", "gegen",
        "für", "an", "auf", "in", "um", "zu", "bis",
    }
    
    # Custom stopwords for medical/technical context (to exclude from keyword extraction)
    CUSTOM_STOPWORDS: Set[str] = {
        # Medical context common words
        "patient", "patienten", "arzt", "ärzte", "mediziner", "therapie", "behandlung",
        "diagnose", "untersuchung", "labor", "klinik", "krankenhaus", "praxis",
        "fall", "fälle", "gruppe", "person", "personen", "patientin", "patientinnen",
        "ergebnis", "ergebnisse", "wert", "werte", "test", "tests", "prüfung",
        # Technical context common words
        "datei", "dateien", "ordner", "verzeichnis", "pfad", "pfade", "name", "namen",
        "typ", "typus", "format", "formate", "größe", "länge", "breite", "höhe",
        "anzahl", "menge", "summe", "teil", "teile", "stück", "stücke",
        "art", "weise", "weg", "seite", "seiten",
        # General filler words
        "gibt", "gab", "gengen", "finden", "fand", "liegen", "lag", "stehen", "stand",
        "geht", "ging", "kommt", "kam", "bleibt", "blieb",
    }
    
    def __init__(
        self,
        use_nltk: bool = True,
        use_custom: bool = True,
        min_word_length: int = 2
    ):
        """
        Initialize StopwordHandler.
        
        Args:
            use_nltk: Try to load NLTK German stopwords (recommended)
            use_custom: Include custom stopwords
            min_word_length: Minimum word length to consider (shorter ignored)
        """
        self.min_word_length = min_word_length
        self._stopwords: Set[str] = set()
        
        # Load NLTK stopwords if available
        if use_nltk:
            self._load_nltk_stopwords()
        
        # Add minimal German stopwords as fallback
        self._stopwords.update(self.MINIMAL_GERMAN_STOPWORDS)
        
        # Add custom stopwords
        if use_custom:
            self._stopwords.update(self.CUSTOM_STOPWORDS)
        
        logger.info(f"StopwordHandler init: {len(self._stopwords)} stopwords loaded")
    
    def _load_nltk_stopwords(self) -> None:
        """Load German stopwords from NLTK."""
        try:
            import nltk
            try:
                nltk.data.find('corpora/stopwords')
            except LookupError:
                # Download if not present
                nltk.download('stopwords', quiet=True)
            
            from nltk.corpus import stopwords
            
            # Get German stopwords
            german_stopwords = set(stopwords.words('german'))
            
            # Filter out words with apostrophes or special characters
            clean_german = {
                w for w in german_stopwords 
                if "'" not in w and len(w) >= 2
            }
            
            self._stopwords.update(clean_german)
            logger.info(f"NLTK German stopwords: {len(clean_german)} words")
            
        except ImportError:
            logger.warning("NLTK not available, using minimal stopwords")
        except Exception as e:
            logger.warning(f"NLTK stopwords error: {e}")
    
    def is_stopword(self, word: str) -> bool:
        """
        Check if a word is a stopword.
        
        Args:
            word: Word to check (case-insensitive)
            
        Returns:
            True if word is a stopword
        """
        if not word:
            return True
        
        clean = word.lower().strip()
        
        # Check length
        if len(clean) < self.min_word_length:
            return True
        
        return clean in self._stopwords
    
    def filter_stopwords(self, words: List[str]) -> List[str]:
        """
        Filter stopwords from a list of words.
        
        Args:
            words: List of words to filter
            
        Returns:
            List without stopwords
        """
        return [w for w in words if not self.is_stopword(w)]
    
    def extract_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        """
        Extract keywords from text, excluding stopwords.
        
        Simple extraction based on:
        1. Split text into tokens
        2. Filter stopwords
        3. Filter short words
        4. Return top N by frequency
        
        Args:
            text: Input text
            max_keywords: Maximum keywords to return
            
        Returns:
            List of keyword strings
        """
        if not text:
            return []
        
        # Tokenize (simple whitespace + punctuation)
        import re
        tokens = re.findall(r'\b\w+\b', text.lower())
        
        # Filter
        filtered = self.filter_stopwords(tokens)
        
        # Count frequency
        from collections import Counter
        freq = Counter(filtered)
        
        # Get most common
        keywords = [word for word, count in freq.most_common(max_keywords)]
        
        return keywords
    
    def add_stopwords(self, words: List[str]) -> None:
        """
        Add custom words to stopword list.
        
        Args:
            words: List of words to add as stopwords
        """
        for w in words:
            self._stopwords.add(w.lower().strip())
    
    def remove_stopwords(self, words: List[str]) -> None:
        """
        Remove words from stopword list.
        
        Args:
            words: List of words to remove from stopwords
        """
        for w in words:
            self._stopwords.discard(w.lower().strip())
    
    def get_all_stopwords(self) -> Set[str]:
        """Return all stopwords as a set."""
        return self._stopwords.copy()
    
    def count_stopwords(self) -> int:
        """Return number of loaded stopwords."""
        return len(self._stopwords)


# =============================================================================
# Global instance (lazy)
# =============================================================================

_global_handler: Optional[StopwordHandler] = None

def get_stopword_handler(**kwargs) -> StopwordHandler:
    """Get or create global StopwordHandler instance."""
    global _global_handler
    if _global_handler is None:
        _global_handler = StopwordHandler(**kwargs)
    return _global_handler


# =============================================================================
# Main: Quick Test
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Stopword Handler - Quick Test")
    print("=" * 60)
    
    handler = StopwordHandler()
    
    print(f"\n[1] Total Stopwords: {handler.count_stopwords()}")
    
    print("\n[2] Sample Stopwords (first 30):")
    sample = sorted(handler.get_all_stopwords())[:30]
    print(f"   {', '.join(sample)}")
    
    print("\n[3] is_stopword() Tests:")
    test_words = ["der", "und", "in", "Therapie", "MTHFR", "Herzinfarkt", "Blut", "ist"]
    for w in test_words:
        result = handler.is_stopword(w)
        print(f"   '{w}': {result}")
    
    print("\n[4] Keyword Extraction Test:")
    test_text = """
    Der Patient leidet an einer MTHFR Genmutation die zu erhöhtem Homocystein führt.
    Eine Behandlung mit Folsäure und Vitamin B12 kann die Methylierung verbessern.
    Herzinfarkt und Schlaganfall sind mögliche Komplikationen bei Bluthochdruck.
    """
    keywords = handler.extract_keywords(test_text, max_keywords=10)
    print(f"   Text: {test_text[:80]}...")
    print(f"   Keywords: {keywords}")
    
    print("\n[5] Filter Stopwords Test:")
    words = ["der", "Hund", "läuft", "über", "die", "Wiese", "MTHFR"]
    filtered = handler.filter_stopwords(words)
    print(f"   Original: {words}")
    print(f"   Filtered: {filtered}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)