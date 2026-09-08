#!/usr/bin/env python3
"""
semantic_association_audit.py — Detect orphaned factual values without clear semantic labels.

Supports hypothesis C-003: Ambiguous Fact-to-Label Association.

Usage:
    python semantic_association_audit.py --url https://example.com [--html page.html] [--output results.json]
    python semantic_association_audit.py --help

Dependencies: requests, beautifulsoup4, lxml
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("ERROR: 'requests' required. Install: pip install requests", file=sys.stderr)
    sys.exit(1)

try:
    from bs4 import BeautifulSoup, NavigableString
except ImportError:
    print("ERROR: 'beautifulsoup4' required. Install: pip install beautifulsoup4 lxml", file=sys.stderr)
    sys.exit(1)

DEFAULT_TIMEOUT = 15

# Patterns for detecting factual values
PRICE_PATTERN = re.compile(r'[\$€£¥]\s*\d[\d,]*\.?\d*|\d[\d,]*\.?\d*\s*(?:USD|EUR|GBP)')
MEASUREMENT_PATTERN = re.compile(r'\d+\.?\d*\s*(?:kg|lb|lbs|oz|g|mm|cm|m|in|inch|inches|ft|feet|mph|km/h|mAh|W|V|Hz|GB|TB|MB)')
PERCENTAGE_PATTERN = re.compile(r'\d+\.?\d*\s*%')
DURATION_PATTERN = re.compile(r'\d+\.?\d*\s*(?:hours?|hrs?|minutes?|mins?|seconds?|secs?|days?|weeks?|months?|years?)')
DATE_PATTERN = re.compile(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s*\d{4}\b', re.IGNORECASE)
DIMENSION_PATTERN = re.compile(r'\d+\.?\d*\s*[x×]\s*\d+\.?\d*(?:\s*[x×]\s*\d+\.?\d*)?(?:\s*(?:mm|cm|in|inches))?')

VALUE_PATTERNS = {
    "price": PRICE_PATTERN,
    "measurement": MEASUREMENT_PATTERN,
    "percentage": PERCENTAGE_PATTERN,
    "duration": DURATION_PATTERN,
    "date": DATE_PATTERN,
    "dimension": DIMENSION_PATTERN,
}

# Tags that provide semantic association
LABEL_TAGS = {"th", "dt", "label", "caption", "legend"}
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
SEMANTIC_CONTAINER_TAGS = {"table", "dl", "figure", "fieldset"}


def find_factual_values(html: str) -> list:
    """Find candidate factual values in HTML text content."""
    soup = BeautifulSoup(html, "lxml")

    # Remove script/style
    for tag in soup.find_all(["script", "style", "noscript"]):
        tag.decompose()

    values = []
    seen = set()

    for element in soup.find_all(text=True):
        if not isinstance(element, NavigableString):
            continue

        parent = element.parent
        if not parent or parent.name in ("script", "style", "noscript"):
            continue

        text = str(element).strip()
        if not text or len(text) > 500:
            continue

        for value_type, pattern in VALUE_PATTERNS.items():
            for match in pattern.finditer(text):
                value_text = match.group().strip()
                if value_text in seen:
                    continue
                seen.add(value_text)

                values.append({
                    "value": value_text,
                    "type": value_type,
                    "parent_tag": parent.name,
                    "parent_classes": parent.get("class", []),
                    "element": parent,  # Keep reference for analysis
                })

    return values


def check_semantic_association(element, soup) -> dict:
    """Check if an element has a clear semantic label association."""
    association = {
        "has_table_header": False,
        "has_definition_term": False,
        "has_label": False,
        "has_heading": False,
        "has_aria": False,
        "has_adjacent_label": False,
        "nearest_label": None,
        "association_quality": "none",
    }

    if element is None:
        return association

    # Check if inside a table with headers
    parent_td = element.find_parent("td")
    if parent_td:
        parent_tr = parent_td.find_parent("tr")
        parent_table = parent_td.find_parent("table")
        if parent_table:
            # Check for <th> in same table
            ths = parent_table.find_all("th")
            if ths:
                association["has_table_header"] = True
                # Try to find corresponding header
                if parent_tr:
                    cells = parent_tr.find_all(["td", "th"])
                    idx = list(cells).index(parent_td) if parent_td in cells else -1
                    if idx >= 0:
                        header_row = parent_table.find("tr")
                        if header_row:
                            headers = header_row.find_all("th")
                            if idx < len(headers):
                                association["nearest_label"] = headers[idx].get_text(strip=True)[:100]

    # Check if inside a <dl> with <dt>
    parent_dd = element.find_parent("dd")
    if parent_dd:
        prev = parent_dd.find_previous_sibling("dt")
        if prev:
            association["has_definition_term"] = True
            association["nearest_label"] = prev.get_text(strip=True)[:100]

    # Check ARIA attributes
    aria_label = element.get("aria-label") if hasattr(element, "get") else None
    aria_describedby = element.get("aria-describedby") if hasattr(element, "get") else None
    if aria_label:
        association["has_aria"] = True
        association["nearest_label"] = aria_label[:100]
    elif aria_describedby:
        association["has_aria"] = True
        described = soup.find(id=aria_describedby)
        if described:
            association["nearest_label"] = described.get_text(strip=True)[:100]

    # Check for nearby heading
    for heading_tag in HEADING_TAGS:
        heading = element.find_previous(heading_tag)
        if heading:
            association["has_heading"] = True
            if not association["nearest_label"]:
                association["nearest_label"] = heading.get_text(strip=True)[:100]
            break

    # Check for adjacent label-like sibling
    if hasattr(element, "find_previous_sibling"):
        prev_sib = element.find_previous_sibling()
        if prev_sib:
            sib_text = prev_sib.get_text(strip=True)
            if sib_text and len(sib_text) < 50 and not any(p.search(sib_text) for p in VALUE_PATTERNS.values()):
                association["has_adjacent_label"] = True
                if not association["nearest_label"]:
                    association["nearest_label"] = sib_text[:100]

    # Determine quality
    if association["has_table_header"] or association["has_definition_term"] or association["has_label"]:
        association["association_quality"] = "strong"
    elif association["has_aria"]:
        association["association_quality"] = "strong"
    elif association["has_adjacent_label"]:
        association["association_quality"] = "moderate"
    elif association["has_heading"]:
        association["association_quality"] = "weak"
    else:
        association["association_quality"] = "none"

    return association


def check_jsonld_coverage(html: str, value: str) -> bool:
    """Check if a value appears in any JSON-LD on the page."""
    soup = BeautifulSoup(html, "lxml")
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            content = script.string or ""
            if value in content:
                return True
        except Exception:
            pass
    return False


def run_audit(html: str, url: str = "") -> dict:
    """Run the semantic association audit."""
    audit_start = datetime.now(timezone.utc).isoformat()

    soup = BeautifulSoup(html, "lxml")

    # Find factual values
    values = find_factual_values(html)

    # Analyze each value
    orphaned_values = []
    well_associated = []

    for v in values:
        element = v.pop("element")  # Remove non-serializable element
        association = check_semantic_association(element, soup)
        has_jsonld = check_jsonld_coverage(html, v["value"])

        v["association"] = {k: val for k, val in association.items()}
        v["has_jsonld_coverage"] = has_jsonld

        if association["association_quality"] == "none" and not has_jsonld:
            orphaned_values.append(v)
        else:
            well_associated.append(v)

    # Severity
    total_values = len(values)
    total_orphaned = len(orphaned_values)

    if total_orphaned == 0:
        status = "pass"
        severity = None
    elif total_orphaned >= 5:
        status = "finding"
        severity = "medium"
    elif total_orphaned >= 2:
        status = "finding"
        severity = "low"
    else:
        status = "uncertain"
        severity = "info"

    return {
        "check_id": "C-003",
        "site": url,
        "timestamp": audit_start,
        "status": status,
        "severity": severity,
        "evidence": {
            "total_factual_values_found": total_values,
            "well_associated": len(well_associated),
            "orphaned_values": total_orphaned,
            "orphaned_details": orphaned_values[:20],
            "value_type_breakdown": {},
        },
        "reason": (
            f"Found {total_values} factual values; {total_orphaned} lack clear semantic label association."
            if total_orphaned > 0
            else f"Found {total_values} factual values; all have clear semantic associations."
        ),
        "suggested_action": {
            "summary": (
                "Associate important factual values with explicit semantic labels using "
                "<table>/<th>, <dl>/<dt>/<dd>, <label>, or ARIA attributes. "
                "Alternatively, provide JSON-LD that maps values to schema.org properties."
            ),
            "priority": severity,
        } if status == "finding" else None,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Audit semantic fact-to-label associations (C-003).",
    )
    parser.add_argument("--url", help="URL to fetch and audit")
    parser.add_argument("--html", help="Path to HTML file to audit")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)

    args = parser.parse_args()

    if args.html:
        with open(args.html, "r", encoding="utf-8") as f:
            html = f.read()
        url = args.url or "local-file"
    elif args.url:
        resp = requests.get(args.url, timeout=args.timeout,
                            headers={"User-Agent": "Mozilla/5.0 (compatible; AuditBot/1.0)"})
        html = resp.text
        url = args.url
    else:
        print("ERROR: Provide --url or --html", file=sys.stderr)
        sys.exit(1)

    result = run_audit(html, url)

    output_json = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
