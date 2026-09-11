#!/usr/bin/env python3
"""
check_render_factual_content.py — C-001 Render-Dependent Content Check.

Compares raw HTML content against structured data (JSON-LD) to detect
factual content that may only be accessible via JavaScript rendering.
Uses requests + BeautifulSoup (no browser automation).
"""
import sys
import json
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; C-Extractability-Audit/1.0)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def get_raw_html(url: str) -> str:
    """Fetch raw HTML without executing JavaScript."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"Error fetching raw HTML: {e}", file=sys.stderr)
        return ""


def extract_structural_texts(html: str) -> list:
    """Extract meaningful text blocks from structural HTML tags."""
    soup = BeautifulSoup(html, "html.parser")
    texts = []
    for tag in soup.find_all(["p", "li", "td", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "dd", "dt"]):
        text = tag.get_text(strip=True)
        if text and len(text) > 30 and len(text.split()) > 4:
            texts.append(text)
    return texts


def detect_spa_shell(html: str) -> bool:
    """Detect if the page is an un-rendered SPA shell with minimal content."""
    soup = BeautifulSoup(html, "html.parser")
    spa_ids = {"root", "app", "__next", "__nuxt"}
    for sid in spa_ids:
        el = soup.find(id=sid)
        if el:
            text = el.get_text(separator=" ", strip=True)
            if len(text.split()) < 30:
                body_text = soup.body.get_text(separator=" ", strip=True) if soup.body else ""
                if len(body_text.split()) < 100:
                    return True
    return False


def check_render_factual_content(url: str):
    raw_html = get_raw_html(url)
    if not raw_html:
        return {"findings": []}

    structural_texts = extract_structural_texts(raw_html)
    is_spa = detect_spa_shell(raw_html)

    findings = []

    if is_spa:
        findings.append({
            "id": "C-001",
            "title": "Render-Dependent Factual Content (SPA Shell Detected)",
            "severity": "high",
            "evidence": (
                f"The page appears to be a client-side rendered SPA shell "
                f"(detected SPA mount point with minimal static content). "
                f"Only {len(structural_texts)} meaningful text blocks found in raw HTML. "
                f"Factual content is likely only available after JavaScript execution, "
                f"making it invisible to AI crawlers that parse raw HTML."
            ),
            "suggested_action": {
                "summary": "Server-render critical factual content (like product specs and primary text) into the initial HTML payload (via SSR or SSG) so it is accessible to machine readers without JavaScript execution.",
                "priority": "high"
            }
        })
    elif len(structural_texts) < 3:
        findings.append({
            "id": "C-001",
            "title": "Render-Dependent Factual Content (Sparse Static Content)",
            "severity": "medium",
            "evidence": (
                f"Only {len(structural_texts)} meaningful text blocks found in the raw HTML payload. "
                f"This may indicate that significant content is loaded dynamically via JavaScript "
                f"and would be invisible to AI crawlers parsing raw HTML."
            ),
            "suggested_action": {
                "summary": "Server-render critical factual content into the initial HTML payload (via SSR or SSG) so it is accessible to machine readers without JavaScript execution.",
                "priority": "medium"
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
