"""
Synonym Expansion for Knowledge Base Query Processing
=====================================================

Phase 2: SynonymExpander with medical/technical thesaurus.
Expands queries before search for better recall.

Source: KB_Erweiterungs_Plan.md (Phase 2)
"""

import logging
from typing import Optional
from .stopwords import StopwordHandler

logger = logging.getLogger(__name__)


class SynonymExpander:
    """
    Query expansion via medical and technical synonyms.
    
    Expands query terms before search to improve recall.
    For example:
    - "Herzinfarkt" → "Herzinfarkt Herzattacke myocardial infarction heart attack"
    - "Bluthochdruck" → "Bluthochdruck Hypertension arterielle Hypertonie"
    
    Two-tier approach:
    1. Exact synonym lookup (fast)
    2. Conceptual expansion (slower, optional)
    """
    
    # Medical synonyms (German → [German synonyms, English synonyms])
    MEDICAL_SYNONYMS = {
        # Cardiovascular
        "herzinfarkt": ["herzattacke", "myokardinfarkt", "myocardial infarction", "heart attack", "herzinfarkt"],
        "bluthochdruck": ["hypertonie", "arterielle hypertonie", "hypertension", "high blood pressure", "blutdruck"],
        "herzinsuffizienz": ["herzschwäche", "heart failure", "chf", "chronic heart failure"],
        "schlaganfall": ["apoplex", "stroke", "cerebral infarct", "brain attack", " cerebrovascular accident"],
        "thrombose": ["blutgerinnsel", "venous thrombosis", "blood clot"],
        "embolie": ["lungenembolie", "pulmonary embolism", "clot"],
        
        # Metabolic / Genetic
        "mthfr": ["methylenetetrahydrofolate reductase", "methylierungsenzym", "mthfr mutation"],
        "genmutation": ["genetische mutation", "dna mutation", "genetic defect", "allel variant"],
        "methylierung": ["dna methylation", "epigenetic modification", "methyl groups"],
        "folsäure": ["folat", "vitamin b9", "folic acid", "folate"],
        "homocystein": ["hcy", "homocysteine", "aminosäure"],
        "cobalamin": ["vitamin b12", "cobalamin", "cobalamine"],
        
        # Inflammation / Immune
        "entzündung": ["inflammation", "inflammatory response", "swelling"],
        "chronisch": ["chronic", "long-term", "langfristig", "persistent"],
        "akut": ["acute", "sudden", "plötzlich", "severe"],
        "autoimmun": ["autoimmune", "autoimmunerkrankung", "immune mediated"],
        
        # Mental Health / Neurology
        "depression": ["depressive disorder", "major depression", "melancholia", "low mood"],
        "angst": ["anxiety", "panic", "phobia", "fear", "anfall"],
        "migräne": ["migraine", "headache", "cephalalgia"],
        "demenz": ["dementia", "alzheimer", "cognitive decline", "gedächtnisverlust"],
        "schlafstörung": ["insomnia", "sleep disorder", "sleep problems"],
        
        # Pain
        "schmerz": ["pain", "ache", "discomfort", "nociception"],
        "kopfschmerz": ["headache", "cephalalgia", "migräne"],
        "rückenschmerz": ["back pain", "lumbago", "dorsalgia"],
        
        # Lab values
        "blutwert": ["lab value", "blood test", "laborwert", "serum marker"],
        "cholesterin": ["cholesterol", "lipid profile", "blutfett"],
        "triglyceride": ["tg", "triacylglycerol", "blood fat"],
        "blutzucker": ["glucose", "blood sugar", "glykämie", "hb1ac"],
        
        # General medical
        "behandlung": ["treatment", "therapy", "therapie", "therapy"],
        "diagnose": ["diagnosis", "diagnostik", "identification"],
        "therapie": ["treatment", "therapy", "behandlung", "intervention"],
        "medikament": ["medication", "drug", "arzneimittel", "pharmaceutical"],
        "nebenwirkung": ["side effect", "adverse effect", "unerwünschte wirkung"],
        "untersuchung": ["examination", "diagnostic test", "analysis", "test"],
        "labor": ["lab", "laboratory", "diagnostics"],
        
        # German/English common medical terms
        "krankenhaus": ["hospital", "clinic", "stationäre behandlung"],
        "arzt": ["physician", "doctor", "mediziner", "practitioner"],
        "patient": ["patient", "subject", "betroffene"],
        "symptom": ["symptom", "sign", "clinical manifestation"],
        "ursache": ["cause", "etiology", "aetiology", "grund"],
    }
    
    # Technical / Computing synonyms
    TECHNICAL_SYNONYMS = {
        # AI / ML / Data
        "ki": ["künstliche intelligenz", "artificial intelligence", "ai", "machine learning", "ml"],
        "maschinelles lernen": ["machine learning", "ml", "statistical learning", "ml"],
        "deep learning": ["deep learning", "neuronale netze", "neural networks", "dl"],
        "neuronales netz": ["neural network", "ann", "deep network"],
        "embedding": ["word embedding", "vector embedding", "text embedding", "sentence embedding"],
        "transformer": ["transformer model", "attention mechanism", "bert", "gpt"],
        "large language model": ["llm", "language model", "foundational model", "generative ai"],
        
        # Search / Retrieval
        "vektordatenbank": ["vector database", "vector store", "vector search", "embedding database"],
        "suchmaschine": ["search engine", "search", "retrieval system"],
        "semantische suche": ["semantic search", "meaning-based search", "neural search", "dense retrieval"],
        "hybridsuche": ["hybrid search", "combined search", "hybrid retrieval"],
        "keyword suche": ["keyword search", "exact match", "bm25", "sparse search"],
        "retrieval": ["retrieval", "information retrieval", "ir", "search and retrieval"],
        
        # ChromaDB specific
        "chroma": ["chroma db", "chromadb", "vector database"],
        "collection": ["chroma collection", "vector collection", "embedding collection"],
        
        # Database / Storage
        "datenbank": ["database", "db", "sql database", "relational database"],
        "sqlite": ["sqlite", "sqlite3", "sql db"],
        "full-text": ["full text search", "fts", "text search", "fts5"],
        "index": ["index", "search index", "lookup index"],
        
        # Obsidian / Markdown
        "obsidian": ["obsidian vault", "markdown notes", "second brain", "zettelkasten"],
        "markdown": ["md", "markdown file", "md file"],
        "vault": ["vault", "knowledge vault", "note collection"],
        "note": ["note", "markdown note", "knowledge note", "zettel"],
        
        # Development
        "framework": ["code framework", "software framework", "development framework"],
        "api": ["application programming interface", "rest api", "web api"],
        "plugin": ["plugin", "extension", "add-on", "module"],
        "integration": ["integration", "connect", "plugin", "interface"],
        "pipeline": ["pipeline", "data pipeline", "processing pipeline", "workflow"],
        "workflow": ["workflow", "process flow", "pipeline", "task flow"],
        
        # PDF / OCR
        "pdf": ["portable document format", "pdf document", "scanned document"],
        "ocr": ["optical character recognition", "text recognition", "scanning", "text extraction"],
        "dokument": ["document", "file", "paper", "text document"],
        
        # General tech
        "software": ["software", "program", "anwendung", "application"],
        "hardware": ["hardware", "computer hardware", "system"],
        "server": ["server", "host", "backend", "server system"],
        "cloud": ["cloud", "cloud computing", "cloud service"],
        "netzwerk": ["network", "computer network", "netz"],
    }
    
    def __init__(self, use_medial: bool = True, use_technical: bool = True):
        """
        Initialize SynonymExpander.
        
        Args:
            use_medial: Include medical synonyms
            use_technical: Include technical synonyms
        """
        self.use_medial = use_medial
        self.use_technical = use_technical
        self.stopword_handler = StopwordHandler()
        
        # Build combined lookup
        self._synonym_map: dict[str, list[str]] = {}
        if use_medial:
            self._synonym_map.update(self.MEDICAL_SYNONYMS)
        if use_technical:
            self._synonym_map.update(self.TECHNICAL_SYNONYMS)
        
        logger.info(f"SynonymExpander init: {len(self._synonym_map)} base terms")
    
    def _clean_term(self, term: str) -> str:
        """Clean and normalize a term."""
        return term.lower().strip()
    
    def _is_stopword(self, term: str) -> bool:
        """Check if term is a stopword."""
        return self.stopword_handler.is_stopword(term)
    
    def expand_term(self, term: str) -> list[str]:
        """
        Expand a single term with synonyms.
        
        Args:
            term: Single term to expand
            
        Returns:
            List including original term and all synonyms
        """
        clean = self._clean_term(term)
        if not clean or self._is_stopword(clean):
            return [clean] if clean else []
        
        if clean in self._synonym_map:
            synonyms = self._synonym_map[clean]
            return [clean] + synonyms
        
        return [clean]
    
    def expand_query(
        self, 
        query: str, 
        include_original: bool = True
    ) -> str:
        """
        Expand a full query string with synonyms.
        
        Args:
            query: Query string to expand
            include_original: Include original terms in expanded query
            
        Returns:
            Expanded query string with synonyms added
        """
        if not query or not query.strip():
            return query
        
        # Parse terms (simple whitespace split)
        terms = query.split()
        expanded_terms = []
        
        for term in terms:
            clean = self._clean_term(term)
            
            # Skip very short terms
            if len(clean) < 2:
                expanded_terms.append(term)
                continue
            
            # Skip stopwords
            if self._is_stopword(clean):
                expanded_terms.append(term)
                continue
            
            # Expand
            synonyms = self.expand_term(clean)
            
            if include_original:
                expanded_terms.append(term)
            
            # Add synonyms (without duplicates)
            for syn in synonyms:
                if syn not in [t.lower() for t in expanded_terms]:
                    expanded_terms.append(syn)
        
        return " ".join(expanded_terms)
    
    def get_synonyms(self, term: str) -> list[str]:
        """
        Get all synonyms for a term (without original).
        
        Args:
            term: Term to look up
            
        Returns:
            List of synonyms (not including original)
        """
        clean = self._clean_term(term)
        return self._synonym_map.get(clean, [])
    
    def has_synonyms(self, term: str) -> bool:
        """Check if a term has known synonyms."""
        return self._clean_term(term) in self._synonym_map
    
    def add_custom_synonym(
        self, 
        term: str, 
        synonyms: list[str],
        category: str = "custom"
    ) -> None:
        """
        Add custom synonyms at runtime.
        
        Args:
            term: Base term (lowercase)
            synonyms: List of synonym terms
            category: Category label (for debugging)
        """
        clean = self._clean_term(term)
        if clean in self._synonym_map:
            # Merge with existing
            existing = set(self._synonym_map[clean])
            existing.update(synonyms)
            self._synonym_map[clean] = list(existing)
        else:
            self._synonym_map[clean] = synonyms
        
        logger.info(f"Added {len(synonyms)} custom synonyms for '{term}' ({category})")


# =============================================================================
# Global instance (lazy)
# =============================================================================

_global_expander: Optional[SynonymExpander] = None

def get_expander(**kwargs) -> SynonymExpander:
    """Get or create global SynonymExpander instance."""
    global _global_expander
    if _global_expander is None:
        _global_expander = SynonymExpander(**kwargs)
    return _global_expander


def expand_query(query: str, **kwargs) -> str:
    """
    Convenience function to expand a query.
    
    Args:
        query: Query string to expand
        **kwargs: Passed to SynonymExpander
        
    Returns:
        Expanded query string
    """
    return get_expander(**kwargs).expand_query(query)


# =============================================================================
# Main: Quick Test
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Synonym Expander - Quick Test")
    print("=" * 60)
    
    expander = SynonymExpander()
    
    # Test medical terms
    test_queries = [
        "herzinfarkt behandlung",
        "bluthochdruck medikamente",
        "mthfr mutation methylierung",
        "diabetes symptome",
        "ki suchmaschine vektordatenbank",
        "obsidian vault markdown",
    ]
    
    print("\n[1] Query Expansion Tests:")
    for q in test_queries:
        expanded = expander.expand_query(q)
        print(f"\n   Original: {q}")
        print(f"   Expanded: {expanded}")
    
    print("\n[2] Single Term Lookup:")
    for term in ["herzinfarkt", "ki", "embedding", "mthfr"]:
        syns = expander.get_synonyms(term)
        print(f"   '{term}' → {syns[:5]}{'...' if len(syns) > 5 else ''}")
    
    print("\n[3] Custom Synonym Addition:")
    expander.add_custom_synonym("test", ["probe", "versuch", "examination"], "test_category")
    print(f"   Added 'test' → {expander.get_synonyms('test')}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)