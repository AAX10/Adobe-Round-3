#!/usr/bin/env python3
import sys
import json
import urllib.request
import urllib.error
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def get_raw_html(url: str) -> str:
    """Fetch raw HTML without executing JavaScript."""
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (compatible; C-Extractability-Audit/1.0)'}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error fetching raw HTML: {e}", file=sys.stderr)
        return ""

def get_rendered_texts(url: str):
    """Render the page using Playwright and extract structural text blocks."""
    rendered_html = ""
    texts = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent='Mozilla/5.0 (compatible; C-Extractability-Audit/1.0)')
            page = context.new_page()
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            rendered_html = page.content()
            
            # Extract texts from meaningful structural tags
            # We use evaluate to get the visible text content from specific tags
            elements = page.eval_on_selector_all(
                "p, li, td, h1, h2, h3, h4, h5, h6, blockquote, dd, dt",
                "elements => elements.map(e => e.innerText.trim())"
            )
            
            # Filter out empty or very short strings (likely UI chrome like "Home" or "Cart")
            for text in elements:
                if text and len(text) > 30 and len(text.split()) > 4:
                    texts.append(text)
                    
            browser.close()
    except PlaywrightTimeoutError:
        print(f"Playwright timeout rendering {url}", file=sys.stderr)
    except Exception as e:
        print(f"Playwright error rendering {url}: {e}", file=sys.stderr)

    return rendered_html, texts

def check_render_factual_content(url: str):
    raw_html = get_raw_html(url)
    if not raw_html:
        return {"findings": []}
        
    rendered_html, rendered_texts = get_rendered_texts(url)
    
    if not rendered_texts:
        return {"findings": []}
        
    # Clean raw html slightly to help matching (normalize spaces)
    normalized_raw_html = re.sub(r'\s+', ' ', raw_html).strip()
    
    missing_facts = []
    
    for text in set(rendered_texts):
        # Normalize the text block for comparison
        normalized_text = re.sub(r'\s+', ' ', text).strip()
        
        # Check if this exact text string exists anywhere in the raw HTML
        if normalized_text not in normalized_raw_html:
            # Try a slightly looser check in case of minor entity encoding differences
            # Just check if the first 20 chars exist
            prefix = normalized_text[:20]
            if prefix not in normalized_raw_html:
                missing_facts.append(normalized_text)
                
    findings = []
    
    if missing_facts:
        ratio = len(missing_facts) / len(set(rendered_texts))
        severity = "high" if ratio > 0.5 else "medium"
        
        # Limit evidence to top 3 missing facts for readability
        evidence_samples = "\\n- ".join(missing_facts[:3])
        evidence_str = (
            f"Detected {len(missing_facts)} out of {len(set(rendered_texts))} factual text blocks "
            f"({ratio*100:.1f}%) that are ONLY available after JavaScript rendering. "
            f"They are completely missing from the raw HTML payload.\\n"
            f"Samples of missing text:\\n- {evidence_samples}"
        )
        
        findings.append({
            "id": "C-001",
            "title": "Render-Dependent Factual Content",
            "severity": severity,
            "evidence": evidence_str,
            "suggested_action": {
                "summary": "Server-render critical factual content (like product specs and primary text) into the initial HTML payload (via SSR or SSG) so it is accessible to machine readers without JavaScript execution.",
                "priority": severity
            }
        })

    return {"findings": findings}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"findings": []}))
        sys.exit(0)
        
    url = sys.argv[1]
    result = check_render_factual_content(url)
    print(json.dumps(result, indent=2))
