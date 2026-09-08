#!/usr/bin/env python3
"""
fact_inventory.py — Extract and classify candidate important facts from a page.

Supports extractability hypotheses (C-001, C-002, C-003).

Usage:
    python fact_inventory.py --url https://example.com [--output results.json]
    python fact_inventory.py --html page.html [--output results.json]
"""

import argparse
import json
import re
import sys
from bs4 import BeautifulSoup

try:
    import requests
except ImportError:
    requests = None

FACT_PATTERNS = {
    "price": re.compile(r'[\$€£¥]\s*\d[\d,]*\.?\d*'),
    "measurement": re.compile(r'\d+\.?\d*\s*(?:kg|lb|oz|g|mm|cm|m|in|ft|mph|km/h|mAh|Wh?|V|Hz|GB|TB|MB)\b'),
    "percentage": re.compile(r'\d+\.?\d*\s*%'),
    "duration": re.compile(r'\d+\.?\d*\s*(?:hours?|hrs?|minutes?|mins?|days?|weeks?|months?|years?)\b'),
    "dimension": re.compile(r'\d+\.?\d*\s*[x×]\s*\d+\.?\d*'),
    "phone": re.compile(r'[\+]?[\d\-\(\)\s]{10,15}'),
    "email": re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
}


def extract_facts(html: str) -> list:
    """Extract candidate factual values from HTML."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    facts = []
    seen = set()

    for fact_type, pattern in FACT_PATTERNS.items():
        for match in pattern.finditer(text):
            value = match.group().strip()
            if value not in seen and len(value) > 1:
                seen.add(value)
                facts.append({"value": value, "type": fact_type, "position": match.start()})

    return sorted(facts, key=lambda x: x["position"])


def classify_page_type(html: str) -> str:
    """Classify page type based on content heuristics."""
    soup = BeautifulSoup(html, "lxml")
    text_lower = soup.get_text(separator=" ", strip=True).lower()

    if any(kw in text_lower for kw in ["add to cart", "buy now", "price", "add to bag"]):
        return "product"
    elif any(kw in text_lower for kw in ["frequently asked", "faq"]):
        return "faq"
    elif any(kw in text_lower for kw in ["pricing", "plans", "per month", "/mo"]):
        return "pricing"
    elif any(kw in text_lower for kw in ["about us", "our mission", "our team"]):
        return "about"
    elif any(kw in text_lower for kw in ["blog", "article", "published", "author"]):
        return "article"
    elif any(kw in text_lower for kw in ["contact", "get in touch", "reach us"]):
        return "contact"
    else:
        return "general"


def main():
    parser = argparse.ArgumentParser(description="Extract and classify facts from a page.")
    parser.add_argument("--url", help="URL to fetch and analyze")
    parser.add_argument("--html", help="Path to HTML file")
    parser.add_argument("--output", help="Output JSON path")

    args = parser.parse_args()

    if args.html:
        with open(args.html, "r", encoding="utf-8") as f:
            html = f.read()
    elif args.url and requests:
        resp = requests.get(args.url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        html = resp.text
    else:
        print("ERROR: Provide --url or --html", file=sys.stderr)
        sys.exit(1)

    facts = extract_facts(html)
    page_type = classify_page_type(html)

    result = {
        "page_type": page_type,
        "total_facts_found": len(facts),
        "facts": facts[:100],
        "type_breakdown": {},
    }

    for f in facts:
        t = f["type"]
        result["type_breakdown"][t] = result["type_breakdown"].get(t, 0) + 1

    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output)


if __name__ == "__main__":
    main()
