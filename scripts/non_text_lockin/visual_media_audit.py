#!/usr/bin/env python3
"""
visual_media_audit.py — Detect video/canvas/interactive elements with facts but no text equivalent.

Supports hypothesis F-003: Non-Text Interactive/Visual Fact Lock-In.

Usage:
    python visual_media_audit.py --url https://example.com [--output results.json]
    python visual_media_audit.py --html page.html [--output results.json]

Dependencies: requests, beautifulsoup4, lxml
"""

import argparse
import json
import sys
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    requests = None

from bs4 import BeautifulSoup

DEFAULT_TIMEOUT = 15


def audit_videos(soup) -> list:
    """Audit video elements for text equivalents."""
    results = []
    for video in soup.find_all("video"):
        tracks = video.find_all("track")
        has_captions = any(
            t.get("kind") in ("captions", "subtitles") for t in tracks
        )
        has_descriptions = any(t.get("kind") == "descriptions" for t in tracks)

        # Check for nearby transcript
        parent = video.find_parent(["section", "article", "div", "figure"])
        nearby_transcript = False
        if parent:
            text = parent.get_text(separator=" ", strip=True).lower()
            nearby_transcript = any(kw in text for kw in ["transcript", "full text", "video text"])

        # Context
        aria_label = video.get("aria-label", "")
        aria_describedby = video.get("aria-describedby", "")
        title = video.get("title", "")

        in_factual = False
        if parent:
            classes = " ".join(parent.get("class", [])).lower()
            in_factual = any(kw in classes for kw in [
                "product", "spec", "feature", "demo", "tutorial", "how-to",
                "instruction", "pricing", "comparison"
            ])

        has_text_equiv = has_captions or has_descriptions or nearby_transcript or bool(aria_label)

        results.append({
            "type": "video",
            "src": (video.get("src") or "")[:200],
            "has_captions": has_captions,
            "has_descriptions": has_descriptions,
            "has_nearby_transcript": nearby_transcript,
            "has_aria_label": bool(aria_label),
            "has_text_equivalent": has_text_equiv,
            "in_factual_area": in_factual,
            "track_count": len(tracks),
            "finding": not has_text_equiv and in_factual,
        })

    return results


def audit_canvas(soup) -> list:
    """Audit canvas elements for text equivalents."""
    results = []
    for canvas in soup.find_all("canvas"):
        # Check fallback content inside canvas tags
        fallback_text = canvas.get_text(strip=True)
        has_fallback = bool(fallback_text)

        aria_label = canvas.get("aria-label", "")
        aria_describedby = canvas.get("aria-describedby", "")
        role = canvas.get("role", "")

        # Check if in factual area
        parent = canvas.find_parent(["section", "article", "div", "main"])
        in_factual = False
        if parent:
            classes = " ".join(parent.get("class", [])).lower()
            heading = parent.find(["h1", "h2", "h3", "h4"])
            heading_text = heading.get_text(strip=True).lower() if heading else ""
            in_factual = any(kw in classes + " " + heading_text for kw in [
                "chart", "graph", "data", "visual", "comparison", "spec", "pricing"
            ])

        # Check for nearby data table as equivalent
        has_data_table = False
        if parent:
            tables = parent.find_all("table")
            has_data_table = len(tables) > 0

        has_text_equiv = has_fallback or bool(aria_label) or has_data_table

        results.append({
            "type": "canvas",
            "has_fallback_content": has_fallback,
            "fallback_preview": fallback_text[:100] if fallback_text else None,
            "has_aria_label": bool(aria_label),
            "has_aria_describedby": bool(aria_describedby),
            "role": role,
            "has_nearby_data_table": has_data_table,
            "has_text_equivalent": has_text_equiv,
            "in_factual_area": in_factual,
            "finding": not has_text_equiv and in_factual,
        })

    return results


def audit_embeds(soup) -> list:
    """Audit object/embed/iframe elements."""
    results = []
    for elem in soup.find_all(["object", "embed", "iframe"]):
        src = elem.get("src") or elem.get("data") or ""
        elem_type = elem.get("type", "")
        title = elem.get("title", "")
        aria_label = elem.get("aria-label", "")

        # Skip common non-factual embeds
        is_tracking = any(kw in src.lower() for kw in [
            "analytics", "tracking", "pixel", "ad", "doubleclick", "facebook.com/plugins"
        ])

        if is_tracking:
            continue

        has_text_equiv = bool(title) or bool(aria_label) or bool(elem.get_text(strip=True))

        results.append({
            "type": elem.name,
            "src": src[:200],
            "content_type": elem_type,
            "has_title": bool(title),
            "has_aria_label": bool(aria_label),
            "has_text_equivalent": has_text_equiv,
            "finding": not has_text_equiv,
        })

    return results[:20]


def audit_svg_text(soup) -> list:
    """Check SVGs for extractable text content."""
    results = []
    for svg in soup.find_all("svg"):
        text_elements = svg.find_all("text")
        has_text = len(text_elements) > 0
        text_content = " ".join(t.get_text(strip=True) for t in text_elements)

        aria_label = svg.get("aria-label", "")
        title_elem = svg.find("title")
        desc_elem = svg.find("desc")

        # Only flag large SVGs (likely charts/diagrams, not icons)
        width = svg.get("width", "")
        height = svg.get("height", "")
        viewbox = svg.get("viewBox", "")

        is_large = False
        try:
            if width and int(str(width).replace("px", "")) > 200:
                is_large = True
            if height and int(str(height).replace("px", "")) > 200:
                is_large = True
        except (ValueError, TypeError):
            pass

        if not is_large:
            continue  # Skip small SVGs (icons)

        has_text_equiv = has_text or bool(aria_label) or bool(title_elem) or bool(desc_elem)

        results.append({
            "type": "svg",
            "has_text_elements": has_text,
            "text_preview": text_content[:200] if text_content else None,
            "has_aria_label": bool(aria_label),
            "has_title": bool(title_elem),
            "has_desc": bool(desc_elem),
            "has_text_equivalent": has_text_equiv,
            "is_large": is_large,
            "finding": not has_text_equiv,
        })

    return results[:20]


def run_audit(html: str, url: str = "") -> dict:
    """Run the visual media fact lock-in audit."""
    audit_start = datetime.now(timezone.utc).isoformat()
    soup = BeautifulSoup(html, "lxml")

    video_results = audit_videos(soup)
    canvas_results = audit_canvas(soup)
    embed_results = audit_embeds(soup)
    svg_results = audit_svg_text(soup)

    all_results = video_results + canvas_results + embed_results + svg_results
    flagged = [r for r in all_results if r.get("finding")]

    if len(flagged) == 0:
        status = "pass"
        severity = None
    elif len(flagged) >= 3:
        status = "finding"
        severity = "medium"
    elif len(flagged) >= 1:
        status = "finding"
        severity = "low"
    else:
        status = "pass"
        severity = None

    return {
        "check_id": "F-003",
        "site": url,
        "timestamp": audit_start,
        "status": status,
        "severity": severity,
        "evidence": {
            "videos_found": len(video_results),
            "canvas_found": len(canvas_results),
            "embeds_found": len(embed_results),
            "large_svgs_found": len(svg_results),
            "total_non_text_elements": len(all_results),
            "flagged_elements": len(flagged),
            "flagged_details": flagged[:20],
            "video_details": video_results[:10],
            "canvas_details": canvas_results[:10],
        },
        "reason": (
            f"Found {len(all_results)} non-text media elements; {len(flagged)} "
            f"lack text equivalents in factual content areas."
            if flagged
            else f"Found {len(all_results)} non-text media elements; "
                 f"all have text equivalents or are non-factual."
        ),
        "suggested_action": {
            "summary": (
                "Provide text equivalents for non-text content: add <track> captions for videos, "
                "fallback content for canvas, data tables for charts, and descriptive text for "
                "interactive visualizations."
            ),
            "priority": severity,
        } if status == "finding" else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Audit visual media for fact lock-in (F-003).")
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
