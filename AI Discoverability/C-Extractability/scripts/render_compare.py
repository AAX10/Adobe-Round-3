#!/usr/bin/env python3
"""
render_compare.py — Compare raw HTML vs rendered DOM for content differences.

Supports hypotheses C-001 (factual content) and C-002 (structural metadata).
Refactored from existing compare_raw_rendered.py for CLI reusability.

Usage:
    python render_compare.py --raw raw.html --rendered rendered.html [--output results.json]
    python render_compare.py --help

Dependencies: beautifulsoup4, lxml
"""

import argparse
import json
import sys
from bs4 import BeautifulSoup


def extract_text(html: str) -> str:
    """Extract visible text from HTML, stripping scripts/styles."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(["script", "style", "svg", "noscript"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def extract_json_ld(html: str) -> list:
    """Extract and parse all JSON-LD blocks from HTML."""
    soup = BeautifulSoup(html, "lxml")
    blocks = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            blocks.append(data)
        except (json.JSONDecodeError, TypeError):
            blocks.append({"_parse_error": True, "_raw": str(script.string)[:200]})
    return blocks


def extract_headings(html: str) -> dict:
    """Extract heading hierarchy."""
    soup = BeautifulSoup(html, "lxml")
    headings = {}
    for level in range(1, 7):
        tag = f"h{level}"
        headings[tag] = [h.get_text(strip=True) for h in soup.find_all(tag)]
    return headings


def extract_links(html: str) -> int:
    """Count <a href> links."""
    soup = BeautifulSoup(html, "lxml")
    return len(soup.find_all("a", href=True))


def extract_images(html: str) -> list:
    """Extract image info."""
    soup = BeautifulSoup(html, "lxml")
    return [
        {"src": img.get("src", "")[:200], "alt": img.get("alt", ""), "has_alt": bool(img.get("alt"))}
        for img in soup.find_all("img")
    ]


def compare(raw_html: str, rendered_html: str) -> dict:
    """Compare raw and rendered HTML across multiple dimensions."""
    raw_text = extract_text(raw_html)
    rendered_text = extract_text(rendered_html)

    raw_jsonld = extract_json_ld(raw_html)
    rendered_jsonld = extract_json_ld(rendered_html)

    raw_headings = extract_headings(raw_html)
    rendered_headings = extract_headings(rendered_html)

    raw_links = extract_links(raw_html)
    rendered_links = extract_links(rendered_html)

    raw_images = extract_images(raw_html)
    rendered_images = extract_images(rendered_html)

    # Text delta
    text_length_delta = len(rendered_text) - len(raw_text)
    text_ratio = len(rendered_text) / len(raw_text) if len(raw_text) > 0 else float("inf")

    # JSON-LD delta
    raw_types = []
    for block in raw_jsonld:
        if isinstance(block, dict):
            t = block.get("@type", "unknown")
            raw_types.append(t if isinstance(t, str) else str(t))

    rendered_types = []
    for block in rendered_jsonld:
        if isinstance(block, dict):
            t = block.get("@type", "unknown")
            rendered_types.append(t if isinstance(t, str) else str(t))

    render_only_types = [t for t in rendered_types if t not in raw_types]

    # Heading delta
    heading_delta = {}
    for level in range(1, 7):
        tag = f"h{level}"
        raw_count = len(raw_headings.get(tag, []))
        rendered_count = len(rendered_headings.get(tag, []))
        if raw_count != rendered_count:
            heading_delta[tag] = {"raw": raw_count, "rendered": rendered_count}

    return {
        "text": {
            "raw_length": len(raw_text),
            "rendered_length": len(rendered_text),
            "delta": text_length_delta,
            "ratio": round(text_ratio, 3),
            "significant_delta": abs(text_length_delta) > 500,
        },
        "json_ld": {
            "raw_count": len(raw_jsonld),
            "rendered_count": len(rendered_jsonld),
            "raw_types": raw_types,
            "rendered_types": rendered_types,
            "render_only_types": render_only_types,
            "has_render_dependent_schemas": len(render_only_types) > 0,
        },
        "headings": {
            "delta": heading_delta,
            "has_heading_changes": len(heading_delta) > 0,
        },
        "links": {
            "raw_count": raw_links,
            "rendered_count": rendered_links,
            "delta": rendered_links - raw_links,
        },
        "images": {
            "raw_count": len(raw_images),
            "rendered_count": len(rendered_images),
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Compare raw HTML vs rendered DOM for extractability gaps (C-001, C-002).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--raw", required=True, help="Path to raw HTML file")
    parser.add_argument("--rendered", required=True, help="Path to rendered HTML file")
    parser.add_argument("--output", help="Output JSON file path")

    args = parser.parse_args()

    try:
        with open(args.raw, "r", encoding="utf-8") as f:
            raw_html = f.read()
        with open(args.rendered, "r", encoding="utf-8") as f:
            rendered_html = f.read()
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    result = compare(raw_html, rendered_html)

    output_json = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
