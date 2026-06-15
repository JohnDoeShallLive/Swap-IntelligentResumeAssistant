import spacy
from typing import List, Dict, Any

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import spacy.cli
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def extract_keywords(text: str) -> List[Dict[str, Any]]:
    """
    Extracts domain-specific keywords from the resume text using spaCy.
    Returns a list of dicts with keyword and frequency.
    """
    doc = nlp(text.lower())
    
    # Simple heuristic: extract nouns and proper nouns as keywords
    keywords = {}
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop and token.is_alpha:
            word = token.text
            keywords[word] = keywords.get(word, 0) + 1
            
    # Sort by frequency
    sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
    
    return [{"keyword": k, "count": v} for k, v in sorted_keywords[:20]]
