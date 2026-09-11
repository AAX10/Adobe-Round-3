import json
import sys
import datetime
import re
import os
from bs4 import BeautifulSoup

from utils_nlp import (
    split_sentences, starts_with_anaphoric_pronoun, extract_entity_names,
    find_numeric_claims, is_qualifier_word, calculate_fluff_ratio
)

# Attempt to load fetch_html from source-selection-auditor, with fallback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'source-selection-auditor', 'scripts'))
try:
    from utils_html import fetch_html, detect_spa_placeholder
except ImportError:
    def fetch_html(url_or_path):
        if url_or_path.startswith('http'):
            import urllib.request
            req = urllib.request.Request(url_or_path, headers={'User-Agent': 'Mozilla/5.0'})
            return urllib.request.urlopen(req).read().decode('utf-8')
        with open(url_or_path, 'r', encoding='utf-8') as f:
            return f.read()

def evaluate_qf1_anaphoric_deprivation(soup) -> dict:
    paragraphs = soup.find_all('p')
    total_sentences = 0
    unanchored_sentences = 0
    evidence = []
    
    for p in paragraphs:
        text = p.get_text(separator=' ', strip=True)
        sentences = split_sentences(text)
        para_entities = extract_entity_names(text)
        
        for s in sentences:
            total_sentences += 1
            if starts_with_anaphoric_pronoun(s):
                if not para_entities:
                    unanchored_sentences += 1
                    evidence.append(s)
                    
    apr = 1 - (unanchored_sentences / total_sentences) if total_sentences > 0 else 1.0
    
    severity = 'low'
    if apr < 0.40:
        severity = 'critical'
    elif apr < 0.65:
        severity = 'high'
    elif apr < 0.82:
        severity = 'medium'
        
    return {
        'id': 'H-QF1',
        'name': 'Anaphoric Deprivation',
        'severity': severity,
        'metric_value': round(apr, 3),
        'evidence': evidence[:5]
    }

def evaluate_qf2_severed_qualifiers(soup) -> dict:
    elements = soup.find_all(['p', 'li', 'td'])
    total_claims = 0
    severed_claims = 0
    evidence = []
    
    qualifier_pattern = r'\b(up to|starting at|subject to|excluding|as of|approximately|estimated)\b'
    
    for el in elements:
        text = el.get_text(separator=' ', strip=True)
        claims = find_numeric_claims(text)
        
        has_parent_qualifier = bool(re.search(qualifier_pattern, text, re.IGNORECASE))
        
        for claim in claims:
            total_claims += 1
            if has_parent_qualifier and not claim['has_qualifier']:
                severed_claims += 1
                evidence.append(f"Number {claim['value']} missing qualifier in sentence. Context: {claim['context_snippet']}")
                
    qpi = 1 - (severed_claims / total_claims) if total_claims > 0 else 1.0
    
    severity = 'low'
    if qpi < 0.55:
        severity = 'high'
    elif qpi < 0.80:
        severity = 'medium'
        
    return {
        'id': 'H-QF2',
        'name': 'Severed Qualifiers',
        'severity': severity,
        'metric_value': round(qpi, 3),
        'evidence': evidence[:5]
    }

def evaluate_qf3_bare_numerics(soup) -> dict:
    text = soup.get_text(separator=' ', strip=True)
    claims = find_numeric_claims(text)
    
    bare_count = 0
    evidence = []
    
    for c in claims:
        is_bare = False
        val_lower = c['value'].lower()
        if '%' in val_lower and not c['has_baseline']:
            is_bare = True
        elif '$' in val_lower and not c['has_timeframe']:
            is_bare = True
        elif val_lower.replace(',', '').isdigit() and int(val_lower.replace(',', '')) > 1000 and not c['has_timeframe']:
            is_bare = True
            
        if is_bare:
            bare_count += 1
            evidence.append(c['context_snippet'])
            
    severity = 'none'
    if bare_count > 3:
        severity = 'medium'
    elif bare_count > 0:
        severity = 'low'
        
    return {
        'id': 'H-QF3',
        'name': 'Bare Numerics',
        'severity': severity,
        'metric_value': bare_count,
        'evidence': evidence[:5]
    }

def evaluate_qf4_table_structure(soup) -> dict:
    tables = soup.find_all('table')
    div_grids = soup.find_all('div', class_=re.compile(r'\b(grid|row|col)\b', re.IGNORECASE))
    
    total_tables = len(tables) + (1 if div_grids else 0)
    tables_with_headers = 0
    
    for t in tables:
        if t.find('th') or t.find('caption'):
            tables_with_headers += 1
            
    if div_grids:
        has_headers = False
        for d in div_grids:
            if 'header' in ' '.join(d.get('class', [])).lower():
                has_headers = True
                break
        if has_headers:
            tables_with_headers += 1
            
    tsi = tables_with_headers / total_tables if total_tables > 0 else 1.0
    
    severity = 'low'
    if tsi < 0.50:
        severity = 'high'
    elif tsi < 0.80:
        severity = 'medium'
        
    return {
        'id': 'H-QF4',
        'name': 'Table Structure',
        'severity': severity,
        'metric_value': round(tsi, 3),
        'evidence': []
    }

def evaluate_qf5_fluff_density(soup) -> dict:
    main = soup.find(['main', 'article'])
    if not main:
        main = soup.find('body')
    
    if not main:
        return {'id': 'H-QF5', 'severity': 'low', 'metric_value': 0.0, 'evidence': []}
        
    paragraphs = main.find_all('p', recursive=False)
    if not paragraphs:
        paragraphs = main.find_all('p')
        
    total_ratio = 0
    count = 0
    evidence = []
    
    for p in paragraphs:
        text = p.get_text(separator=' ', strip=True)
        sentences = split_sentences(text)
        for s in sentences:
            r = calculate_fluff_ratio(s)
            total_ratio += r
            count += 1
            if r > 0:
                evidence.append(s)
                
    avg_ratio = (total_ratio / count * 100) if count > 0 else 0.0
    
    severity = 'low'
    if avg_ratio > 2.5:
        severity = 'high'
    elif avg_ratio > 1.5:
        severity = 'medium'
        
    return {
        'id': 'H-QF5',
        'name': 'Fluff Density',
        'severity': severity,
        'metric_value': round(avg_ratio, 3),
        'evidence': evidence[:5]
    }

def evaluate_qf6_accordion_isolation(soup) -> dict:
    details = soup.find_all('details')
    if not details:
        return {'id': 'H-QF6', 'severity': 'none', 'metric_value': 0.0, 'evidence': []}
        
    page_text = soup.get_text(separator=' ', strip=True)
    page_entities = extract_entity_names(page_text)
    
    generic_count = 0
    evidence = []
    
    for d in details:
        summary = d.find('summary')
        if summary:
            s_text = summary.get_text(separator=' ', strip=True)
            s_entities = extract_entity_names(s_text)
            if not (s_entities & page_entities):
                generic_count += 1
                evidence.append(s_text)
                
    generic_ratio = generic_count / len(details)
    
    severity = 'low'
    if generic_ratio > 0.50:
        severity = 'medium'
        
    return {
        'id': 'H-QF6',
        'name': 'Accordion Isolation',
        'severity': severity,
        'metric_value': round(generic_ratio, 3),
        'evidence': evidence[:5]
    }

def proactive_recommendation_generator(apr, qpi, tsi) -> list:
    recs = []
    if apr < 0.65:
        recs.append("Replace vague pronouns with concrete entity names at the start of paragraphs.")
    if qpi < 0.55:
        recs.append("Ensure numeric claims are placed in the same sentence as their qualifiers to avoid misinterpretation.")
    if tsi < 0.80:
        recs.append("Add <th> elements to tables to provide semantic context for data cells.")
    if not recs:
        recs.append("Maintain high structural clarity for AI consumption.")
    return recs

def run_quote_feasibility_audit(source: str, is_url: bool = False) -> dict:
    """Run all Quote Feasibility hypothesis checks.
    
    Args:
        source: URL or local filepath to audit.
        is_url: Whether the source is a URL (True) or filepath (False).
    """
    if source.endswith('.html') or (os.path.isfile(source) and not is_url):
        with open(source, 'r', encoding='utf-8') as f:
            html = f.read()
    else:
        html = fetch_html(source)

    soup = BeautifulSoup(html, 'html.parser')
    
    qf1 = evaluate_qf1_anaphoric_deprivation(soup)
    qf2 = evaluate_qf2_severed_qualifiers(soup)
    qf3 = evaluate_qf3_bare_numerics(soup)
    qf4 = evaluate_qf4_table_structure(soup)
    qf5 = evaluate_qf5_fluff_density(soup)
    qf6 = evaluate_qf6_accordion_isolation(soup)
    
    apr = qf1.get('metric_value', 1.0)
    qpi = qf2.get('metric_value', 1.0)
    tsi = qf4.get('metric_value', 1.0)
    
    score_qf = 0.40 * apr + 0.35 * qpi + 0.25 * tsi
    
    result = {
        'audited_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'target': source,
        'auditor': 'Quote Feasibility Auditor',
        'score_qf': round(score_qf, 3),
        'metrics': {
            'APR': apr,
            'QPI': qpi,
            'TSI': tsi
        },
        'evaluations': [qf1, qf2, qf3, qf4, qf5, qf6],
        'recommendations': proactive_recommendation_generator(apr, qpi, tsi)
    }
    return result

if __name__ == '__main__':
    import io
    

    if len(sys.argv) < 2:
        print("Usage: python evaluate_quote_feasibility.py <url_or_filepath>")
        sys.exit(1)
        
    target = sys.argv[1]
    is_url = target.startswith('http')
    res = run_quote_feasibility_audit(target, is_url)
    print(json.dumps(res, indent=2))
