import re
from typing import List, Dict, Set

def split_sentences(text: str) -> List[str]:
    """Split text into sentences using regex (handles Mr., Dr., etc.)."""
    # Protect common abbreviations
    text = re.sub(r'\b(Mr|Mrs|Ms|Dr|Prof|Rev|Capt|Lt|Gov|Hon|St|Jr|Sr)\.', r'\1<DOT>', text)
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.replace('<DOT>', '.').strip() for s in sentences if s.strip()]

def starts_with_anaphoric_pronoun(sentence: str) -> bool:
    """Returns True if sentence starts with It/They/This/These/That/Those + verb or noun pattern."""
    pattern = r'^(It|They|This|These|That|Those)\b'
    return bool(re.match(pattern, sentence, re.IGNORECASE))

def extract_entity_names(text: str) -> Set[str]:
    """Extract capitalized multi-word proper nouns as entity candidates."""
    pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
    return set(re.findall(pattern, text))

def find_numeric_claims(text: str) -> List[Dict]:
    """
    Find numbers with %, $, x, users, customers patterns.
    Return {value, unit, context_snippet, has_qualifier, has_baseline, has_timeframe}
    """
    pattern = r'(\$?\d+(?:,\d+)*(?:\.\d+)?(?:%|x|\s*users|\s*customers)?)'
    results = []
    
    matches = re.finditer(pattern, text, re.IGNORECASE)
    for m in matches:
        val = m.group(1)
        start = max(0, m.start() - 40)
        end = min(len(text), m.end() + 40)
        snippet = text[start:end]
        
        qualifiers_pattern = r'\b(up to|starting at|subject to|excluding|as of|approximately|estimated)\b'
        baselines_pattern = r'\b(than|baseline|compared to)\b'
        timeframes_pattern = r'\b(year|month|day|quarter|annual|mo|yr)\b'
        
        results.append({
            'value': val,
            'unit': '',
            'context_snippet': snippet,
            'has_qualifier': bool(re.search(qualifiers_pattern, snippet, re.IGNORECASE)),
            'has_baseline': bool(re.search(baselines_pattern, snippet, re.IGNORECASE)),
            'has_timeframe': bool(re.search(timeframes_pattern, snippet, re.IGNORECASE))
        })
    return results

def is_qualifier_word(word: str) -> bool:
    """Check if word is a qualifier like 'up to', 'starting at', etc."""
    qualifiers = {'up to', 'starting at', 'subject to', 'excluding', 'as of', 'approximately', 'estimated'}
    return word.lower() in qualifiers

def calculate_fluff_ratio(sentence: str) -> float:
    """Count marketing adjectives vs factual nouns/verbs. Return ratio."""
    fluff_words = {
        'innovative', 'cutting-edge', 'revolutionary', 'best-in-class', 
        'world-class', 'seamless', 'robust', 'scalable', 'powerful', 
        'enterprise-grade', 'next-generation', 'state-of-the-art', 
        'unparalleled', 'industry-leading', 'groundbreaking'
    }
    words = [w.lower() for w in re.findall(r'\b\w+\b', sentence)]
    fluff_count = sum(1 for w in words if w in fluff_words)
    total_words = len(words)
    return fluff_count / max(total_words, 1)
