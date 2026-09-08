#!/usr/bin/env python3
"""
structured_data_compare.py — Compare JSON-LD structured data between raw and rendered HTML.

Supports hypothesis C-002: Render-Dependent Structural Metadata.
Refactored from existing extract_structured_data.py with relevance filtering.

Usage:
    python structured_data_compare.py --raw raw.html --rendered rendered.html [--output results.json]
"""

import argparse
import json
import sys
from bs4 import BeautifulSoup

# Schema types considered relevant (not generic)
RELEVANT_SCHEMA_TYPES = {
    "FAQPage", "Product", "Offer", "HowTo", "Recipe", "Event",
    "Article", "NewsArticle", "BlogPosting", "Review", "AggregateRating",
    "LocalBusiness", "Restaurant", "MedicalEntity", "Course",
    "JobPosting", "SoftwareApplication", "VideoObject",
}

# Schema types considered generic/supplementary
GENERIC_SCHEMA_TYPES = {
    "WebSite", "WebPage", "BreadcrumbList", "Organization",
    "SearchAction", "SiteNavigationElement", "ImageObject",
}


def extract_json_ld_typed(html: str) -> list:
    """Extract JSON-LD blocks with type classification."""
    soup = BeautifulSoup(html, "lxml")
    blocks = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            schema_type = data.get("@type", "unknown") if isinstance(data, dict) else "unknown"
            if isinstance(schema_type, list):
                schema_type = schema_type[0] if schema_type else "unknown"

            is_relevant = schema_type in RELEVANT_SCHEMA_TYPES
            is_generic = schema_type in GENERIC_SCHEMA_TYPES

            # Extract meaningful fields
            fields = []
            if isinstance(data, dict):
                for key, val in data.items():
                    if key.startswith("@"):
                        continue
                    if val and str(val).strip():
                        fields.append(key)

            blocks.append({
                "type": schema_type,
                "is_relevant": is_relevant,
                "is_generic": is_generic,
                "field_count": len(fields),
                "fields": fields[:20],
                "data": data,
            })
        except (json.JSONDecodeError, TypeError):
            blocks.append({"type": "parse_error", "is_relevant": False, "is_generic": False})
    return blocks


def compare_structured_data(raw_html: str, rendered_html: str) -> dict:
    """Compare JSON-LD between raw and rendered HTML with relevance filtering."""
    raw_blocks = extract_json_ld_typed(raw_html)
    rendered_blocks = extract_json_ld_typed(rendered_html)

    raw_types = set(b["type"] for b in raw_blocks)
    rendered_types = set(b["type"] for b in rendered_blocks)

    render_only_types = rendered_types - raw_types
    render_only_relevant = [t for t in render_only_types if t in RELEVANT_SCHEMA_TYPES]
    render_only_generic = [t for t in render_only_types if t in GENERIC_SCHEMA_TYPES]

    # Check if render-only schemas contain meaningful fields
    render_only_blocks = [b for b in rendered_blocks if b["type"] in render_only_types]

    # Check text coverage: are the facts in render-only schemas present in raw HTML?
    raw_text = BeautifulSoup(raw_html, "lxml").get_text(separator=" ", strip=True)
    text_coverage = []
    for block in render_only_blocks:
        if not isinstance(block.get("data"), dict):
            continue
        for key, val in block["data"].items():
            if key.startswith("@") or not isinstance(val, str):
                continue
            val_clean = val.strip()[:200]
            if val_clean and len(val_clean) > 3:
                found = val_clean in raw_text
                text_coverage.append({
                    "schema": block["type"],
                    "field": key,
                    "value_preview": val_clean[:100],
                    "in_raw_html": found,
                })

    # Classification
    if render_only_relevant:
        facts_in_html = all(tc["in_raw_html"] for tc in text_coverage if tc["schema"] in RELEVANT_SCHEMA_TYPES) if text_coverage else False
        if facts_in_html:
            classification = "semantic_loss"
        else:
            classification = "information_loss"
    else:
        classification = "pass"

    return {
        "check_id": "C-002",
        "raw_schema_count": len(raw_blocks),
        "rendered_schema_count": len(rendered_blocks),
        "raw_types": sorted(raw_types),
        "rendered_types": sorted(rendered_types),
        "render_only_types": sorted(render_only_types),
        "render_only_relevant": render_only_relevant,
        "render_only_generic": render_only_generic,
        "render_only_blocks_detail": [
            {k: v for k, v in b.items() if k != "data"} for b in render_only_blocks
        ],
        "text_coverage": text_coverage[:30],
        "classification": classification,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Compare JSON-LD structured data between raw and rendered HTML (C-002).",
    )
    parser.add_argument("--raw", required=True, help="Path to raw HTML file")
    parser.add_argument("--rendered", required=True, help="Path to rendered HTML file")
    parser.add_argument("--output", help="Output JSON file path")

    args = parser.parse_args()

    with open(args.raw, "r", encoding="utf-8") as f:
        raw_html = f.read()
    with open(args.rendered, "r", encoding="utf-8") as f:
        rendered_html = f.read()

    result = compare_structured_data(raw_html, rendered_html)

    output_json = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
