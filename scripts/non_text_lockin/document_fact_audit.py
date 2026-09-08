#!/usr/bin/env python3
"""
document_fact_audit.py — Detect important facts locked in downloadable documents without HTML equivalents.

Supports hypothesis F-002: Document-Only Critical Information.

Usage:
    python document_fact_audit.py --url https://example.com [--output results.json]
    python document_fact_audit.py --html page.html [--output results.json]

Dependencies: requests, beautifulsoup4, lxml
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin

try:
    import requests
except ImportError:
    requests = None

from bs4 import BeautifulSoup

DEFAULT_TIMEOUT = 15

# File extensions indicating downloadable documents
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".csv"}

# Link text patterns suggesting factual document content
FACTUAL_DOC_PATTERNS = [
    re.compile(r'spec(?:ification)?s?\b', re.IGNORECASE),
    re.compile(r'price\s*(?:list|sheet)', re.IGNORECASE),
    re.compile(r'data\s*sheet', re.IGNORECASE),
    re.compile(r'product\s*(?:guide|sheet|info)', re.IGNORECASE),
    re.compile(r'technical\s*(?:data|details|info)', re.IGNORECASE),
    re.compile(r'brochure', re.IGNORECASE),
    re.compile(r'menu', re.IGNORECASE),
    re.compile(r'compatibility', re.IGNORECASE),
    re.compile(r'schedule', re.IGNORECASE),
    re.compile(r'catalog(?:ue)?', re.IGNORECASE),
    re.compile(r'rate\s*(?:card|sheet)', re.IGNORECASE),
]

# Patterns suggesting supplementary (non-critical) documents
SUPPLEMENTARY_DOC_PATTERNS = [
    re.compile(r'terms?\s*(?:of|&)\s*(?:service|use|conditions)', re.IGNORECASE),
    re.compile(r'privacy\s*policy', re.IGNORECASE),
    re.compile(r'user\s*(?:manual|guide)', re.IGNORECASE),
    re.compile(r'white\s*paper', re.IGNORECASE),
    re.compile(r'annual\s*report', re.IGNORECASE),
    re.compile(r'press\s*release', re.IGNORECASE),
    re.compile(r'research\s*(?:paper|report)', re.IGNORECASE),
]


def find_document_links(html: str, base_url: str) -> list:
    """Find links to downloadable documents."""
    soup = BeautifulSoup(html, "lxml")
    docs = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "")
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        path = parsed.path.lower()

        # Check file extension
        ext = None
        for doc_ext in DOCUMENT_EXTENSIONS:
            if path.endswith(doc_ext):
                ext = doc_ext
                break

        # Check link text for document indicators
        link_text = a_tag.get_text(strip=True)
        has_download_attr = a_tag.get("download") is not None

        if ext or has_download_attr or any(kw in link_text.lower() for kw in ["download", "pdf", "spec sheet"]):
            if not ext:
                ext = "unknown"

            # Classify importance
            is_factual = any(p.search(link_text) or p.search(href) for p in FACTUAL_DOC_PATTERNS)
            is_supplementary = any(p.search(link_text) for p in SUPPLEMENTARY_DOC_PATTERNS)

            # Get surrounding context
            parent_section = a_tag.find_parent(["section", "article", "div", "main"])
            nearby_heading = a_tag.find_previous(["h1", "h2", "h3", "h4"])

            docs.append({
                "url": full_url[:500],
                "link_text": link_text[:200],
                "file_extension": ext,
                "is_factual_document": is_factual,
                "is_supplementary": is_supplementary,
                "has_download_attr": has_download_attr,
                "nearby_heading": nearby_heading.get_text(strip=True)[:100] if nearby_heading else None,
                "parent_section_class": " ".join(parent_section.get("class", [])) if parent_section else None,
            })

    return docs


def check_html_coverage(html: str, doc: dict) -> dict:
    """Check if the page HTML likely contains facts that the document covers."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(["script", "style"]):
        tag.decompose()
    page_text = soup.get_text(separator=" ", strip=True).lower()

    # Extract keywords from document link text and context
    link_text = doc.get("link_text", "").lower()
    heading = (doc.get("nearby_heading") or "").lower()

    coverage_signals = {
        "has_spec_table": bool(soup.find("table")),
        "has_definition_list": bool(soup.find("dl")),
        "has_pricing_text": any(kw in page_text for kw in ["price", "pricing", "cost", "$", "€", "£"]),
        "has_specification_text": any(kw in page_text for kw in ["specification", "dimensions", "weight", "capacity"]),
        "has_schedule_text": any(kw in page_text for kw in ["hours", "schedule", "open", "available"]),
    }

    # Estimate coverage
    relevant_signals = 0
    if "spec" in link_text or "spec" in heading:
        relevant_signals += 1 if coverage_signals["has_specification_text"] or coverage_signals["has_spec_table"] else 0
    if "price" in link_text or "price" in heading:
        relevant_signals += 1 if coverage_signals["has_pricing_text"] else 0
    if "schedule" in link_text or "hours" in link_text:
        relevant_signals += 1 if coverage_signals["has_schedule_text"] else 0

    return {
        "coverage_signals": coverage_signals,
        "likely_covered_in_html": relevant_signals > 0,
    }


def run_audit(html: str, url: str = "") -> dict:
    """Run the document fact lock-in audit."""
    audit_start = datetime.now(timezone.utc).isoformat()

    doc_links = find_document_links(html, url)
    factual_docs = [d for d in doc_links if d["is_factual_document"] and not d["is_supplementary"]]
    supplementary_docs = [d for d in doc_links if d["is_supplementary"]]

    flagged = []
    for doc in factual_docs:
        coverage = check_html_coverage(html, doc)
        doc["html_coverage"] = coverage
        if not coverage["likely_covered_in_html"]:
            doc["finding"] = True
            flagged.append(doc)
        else:
            doc["finding"] = False

    if len(flagged) == 0:
        status = "pass"
        severity = None
    elif len(flagged) >= 3:
        status = "finding"
        severity = "high"
    elif len(flagged) >= 1:
        status = "finding"
        severity = "medium"
    else:
        status = "uncertain"
        severity = "info"

    return {
        "check_id": "F-002",
        "site": url,
        "timestamp": audit_start,
        "status": status,
        "severity": severity,
        "evidence": {
            "total_document_links": len(doc_links),
            "factual_documents": len(factual_docs),
            "supplementary_documents": len(supplementary_docs),
            "flagged_documents": len(flagged),
            "flagged_details": flagged[:20],
        },
        "reason": (
            f"Found {len(doc_links)} document links; {len(flagged)} factual documents "
            f"appear to contain information not available in the page HTML."
            if flagged
            else f"Found {len(doc_links)} document links; all factual content appears "
                 f"to be available in the page HTML."
        ),
        "suggested_action": {
            "summary": (
                "Provide an HTML text equivalent for critical facts contained in "
                "downloadable documents. Add specification tables, pricing sections, "
                "or structured data directly to the webpage."
            ),
            "priority": severity,
        } if status == "finding" else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Audit documents for fact lock-in (F-002).")
    parser.add_argument("--url", help="URL to fetch and audit")
    parser.add_argument("--html", help="Path to HTML file")
    parser.add_argument("--output", help="Output JSON path")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)

    args = parser.parse_args()

    if args.html:
        with open(args.html, "r", encoding="utf-8") as f:
            html = f.read()
        url = args.url or "local-file"
    elif args.url and requests:
        resp = requests.get(args.url, timeout=args.timeout,
                            headers={"User-Agent": "Mozilla/5.0 (compatible; AuditBot/1.0)"})
        html = resp.text
        url = args.url
    else:
        print("ERROR: Provide --url or --html", file=sys.stderr)
        sys.exit(1)

    result = run_audit(html, url)
    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output)


if __name__ == "__main__":
    main()
