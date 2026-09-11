#!/usr/bin/env python3
"""
image_fact_audit.py — Detect images that may contain important facts without text equivalents.

Supports hypothesis F-001: Image-Only Core Facts.

Usage:
    python image_fact_audit.py --url https://example.com [--output results.json]
    python image_fact_audit.py --html page.html [--output results.json]

Dependencies: requests, beautifulsoup4, lxml
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    requests = None

from bs4 import BeautifulSoup

DEFAULT_TIMEOUT = 15

# Generic/empty alt text patterns
GENERIC_ALT_PATTERNS = [
    re.compile(r'^image$', re.IGNORECASE),
    re.compile(r'^photo$', re.IGNORECASE),
    re.compile(r'^picture$', re.IGNORECASE),
    re.compile(r'^icon$', re.IGNORECASE),
    re.compile(r'^img$', re.IGNORECASE),
    re.compile(r'^banner$', re.IGNORECASE),
    re.compile(r'^hero$', re.IGNORECASE),
    re.compile(r'^thumbnail$', re.IGNORECASE),
    re.compile(r'^\s*$'),
    re.compile(r'^untitled', re.IGNORECASE),
    re.compile(r'^DSC\d+', re.IGNORECASE),
    re.compile(r'^IMG_\d+', re.IGNORECASE),
]

# Filename patterns suggesting factual content
FACTUAL_FILENAME_PATTERNS = [
    re.compile(r'spec', re.IGNORECASE),
    re.compile(r'price', re.IGNORECASE),
    re.compile(r'chart', re.IGNORECASE),
    re.compile(r'table', re.IGNORECASE),
    re.compile(r'diagram', re.IGNORECASE),
    re.compile(r'schedule', re.IGNORECASE),
    re.compile(r'hours', re.IGNORECASE),
    re.compile(r'menu', re.IGNORECASE),
    re.compile(r'comparison', re.IGNORECASE),
    re.compile(r'infographic', re.IGNORECASE),
]

# Tags that suggest factual content areas
FACTUAL_CONTEXT_TAGS = {"main", "article", "section"}


def classify_alt_text(alt: str) -> str:
    """Classify alt text quality."""
    if alt is None:
        return "missing"
    if not alt.strip():
        return "empty"  # Intentionally empty = decorative
    if any(p.match(alt) for p in GENERIC_ALT_PATTERNS):
        return "generic"
    if len(alt) < 5:
        return "minimal"
    return "descriptive"


def get_nearby_text(element, radius: int = 3) -> str:
    """Get text from nearby siblings and parent."""
    texts = []

    # Check figcaption
    parent_figure = element.find_parent("figure")
    if parent_figure:
        caption = parent_figure.find("figcaption")
        if caption:
            texts.append(caption.get_text(strip=True))

    # Previous siblings
    prev = element.find_previous_sibling()
    count = 0
    while prev and count < radius:
        t = prev.get_text(strip=True)
        if t:
            texts.append(t)
        prev = prev.find_previous_sibling()
        count += 1

    # Next siblings
    nxt = element.find_next_sibling()
    count = 0
    while nxt and count < radius:
        t = nxt.get_text(strip=True)
        if t:
            texts.append(t)
        nxt = nxt.find_next_sibling()
        count += 1

    return " ".join(texts)[:500]


def is_in_factual_area(element) -> bool:
    """Check if element is within a factual content area."""
    for parent in element.parents:
        if parent.name in FACTUAL_CONTEXT_TAGS:
            return True
        # Check for product/pricing/spec class names
        classes = " ".join(parent.get("class", []))
        if any(kw in classes.lower() for kw in ["product", "price", "spec", "feature", "detail", "comparison"]):
            return True
    return False


def check_jsonld_coverage(soup, img_src: str) -> bool:
    """Check if JSON-LD on the page might cover the image's factual content."""
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                schema_type = data.get("@type", "")
                if schema_type in ("Product", "Offer", "LocalBusiness", "Restaurant", "Event"):
                    return True
        except Exception:
            pass
    return False


def run_audit(html: str, url: str = "") -> dict:
    """Run the image fact lock-in audit."""
    audit_start = datetime.now(timezone.utc).isoformat()
    soup = BeautifulSoup(html, "lxml")

    images = soup.find_all("img")
    total_images = len(images)

    candidates = []
    well_labeled = []
    decorative = []

    for img in images:
        src = img.get("src", "") or img.get("data-src", "") or ""
        alt = img.get("alt")
        title = img.get("title", "")
        alt_class = classify_alt_text(alt)

        # Skip intentionally decorative (alt="")
        if alt_class == "empty":
            decorative.append({"src": src[:200], "classification": "decorative"})
            continue

        # Skip tiny images (likely icons)
        width = img.get("width", "")
        height = img.get("height", "")
        try:
            if width and int(width) < 50 and height and int(height) < 50:
                decorative.append({"src": src[:200], "classification": "small_icon"})
                continue
        except (ValueError, TypeError):
            pass

        in_factual = is_in_factual_area(img)
        nearby = get_nearby_text(img)
        has_factual_filename = any(p.search(src) for p in FACTUAL_FILENAME_PATTERNS)
        has_jsonld = check_jsonld_coverage(soup, src)

        if alt_class == "descriptive":
            well_labeled.append({
                "src": src[:200],
                "alt": alt[:200] if alt else None,
                "alt_quality": alt_class,
            })
            continue

        # Candidate for finding: poor alt text + factual area
        if (alt_class in ("missing", "generic", "minimal")) and (in_factual or has_factual_filename):
            candidates.append({
                "src": src[:200],
                "alt": alt[:200] if alt else None,
                "alt_quality": alt_class,
                "in_factual_area": in_factual,
                "has_factual_filename": has_factual_filename,
                "nearby_text_preview": nearby[:200],
                "has_jsonld_coverage": has_jsonld,
                "finding": not has_jsonld,  # If JSON-LD covers the area, reduce concern
            })

    flagged = [c for c in candidates if c.get("finding")]

    if len(flagged) == 0:
        status = "pass"
        severity = None
    elif len(flagged) >= 5:
        status = "finding"
        severity = "high"
    elif len(flagged) >= 2:
        status = "finding"
        severity = "medium"
    else:
        status = "finding"
        severity = "low"

    return {
        "check_id": "F-001",
        "site": url,
        "timestamp": audit_start,
        "status": status,
        "severity": severity,
        "evidence": {
            "total_images": total_images,
            "decorative_images": len(decorative),
            "well_labeled_images": len(well_labeled),
            "candidate_factual_images": len(candidates),
            "flagged_images": len(flagged),
            "flagged_details": flagged[:20],
        },
        "reason": (
            f"Found {total_images} images; {len(flagged)} in factual content areas "
            f"lack descriptive alt text and no text equivalent was found."
            if flagged
            else f"Found {total_images} images; all factual images have text equivalents."
        ),
        "suggested_action": {
            "summary": (
                "Provide descriptive alt text for images in factual content areas, "
                "or add equivalent text (caption, table, or JSON-LD) conveying the same facts."
            ),
            "priority": severity,
        } if status == "finding" else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Audit images for fact lock-in (F-001).")
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
