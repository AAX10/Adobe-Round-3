"""
evaluate_source_selection.py — Source Selection Auditor (H-SS1, H-SS2, H-SS3).

Measures whether an AI retriever / RAG chunker can reliably select and extract
the primary factual content of a page without being polluted by layout chrome,
heading-answer disconnects, or cross-boundary proposition splits.

Usage:
    python evaluate_source_selection.py <url_or_filepath>
"""

import json
import sys
import os
import datetime
import re

from bs4 import BeautifulSoup, Tag

# Allow importing sibling utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils_html import (
    fetch_html,
    detect_main_content,
    count_tokens,
    get_container_tokens,
    detect_spa_placeholder,
    extract_headings_with_content,
)


# ---------------------------------------------------------------------------
# H-SS1: Noise-to-Signal / Content Density Ratio
# ---------------------------------------------------------------------------
def evaluate_ss1_content_density(soup: BeautifulSoup) -> dict:
    """MCDR = Main Content Tokens / Parent DOM Container Tokens."""
    main_tag = detect_main_content(soup)
    main_tokens = count_tokens(main_tag.get_text(separator=" ", strip=True)) if main_tag else 0
    container_tokens = get_container_tokens(soup)

    mcdr = main_tokens / container_tokens if container_tokens > 0 else 0.0

    evidence_parts = [
        f"Main content tokens: {main_tokens}.",
        f"Total container tokens: {container_tokens}.",
        f"MCDR = {mcdr:.3f}.",
    ]

    if mcdr < 0.25:
        severity = "critical"
        evidence_parts.append(
            "Page is overwhelmed by boilerplate; RAG retrievers will ingest mostly noise."
        )
    elif mcdr < 0.35:
        severity = "high"
        evidence_parts.append(
            "Significant layout chrome dilutes content signal for AI chunkers."
        )
    elif mcdr < 0.50:
        severity = "medium"
        evidence_parts.append(
            "Moderate boilerplate present; consider stripping non-semantic wrappers."
        )
    else:
        severity = "none"

    return {
        "id": "H-SS1",
        "title": "Noise-to-Signal / Content Density Ratio",
        "severity": severity,
        "score": round(mcdr, 4),
        "evidence": " ".join(evidence_parts),
        "suggested_action": {
            "summary": (
                "Wrap primary factual content in a <main> or <article> tag and move "
                "promotional banners, mega-navs, and footers outside the main content landmark."
            ),
            "priority": severity if severity != "none" else "low",
        },
    }


# ---------------------------------------------------------------------------
# H-SS2: Heading-to-Answer Semantic Locality
# ---------------------------------------------------------------------------
def evaluate_ss2_heading_locality(soup: BeautifulSoup) -> dict:
    """HAL = max(0, 1 - char_distance / 250) for each heading."""
    headings = extract_headings_with_content(soup)

    if not headings:
        return {
            "id": "H-SS2",
            "title": "Heading-to-Answer Semantic Locality",
            "severity": "medium",
            "score": 0.5,
            "evidence": "No headings detected inside main content region.",
            "suggested_action": {
                "summary": "Add semantic headings (h1-h3) to structure your page content.",
                "priority": "medium",
            },
        }

    hal_scores = []
    worst_heading = None
    worst_hal = 1.0

    for h in headings:
        dist = h["char_distance"]
        hal = max(0.0, 1.0 - dist / 250.0)
        hal_scores.append(hal)
        if hal < worst_hal:
            worst_hal = hal
            worst_heading = h

    avg_hal = sum(hal_scores) / len(hal_scores)

    evidence_parts = [
        f"Analyzed {len(headings)} headings.",
        f"Average HAL score: {avg_hal:.2f}.",
    ]

    if worst_heading and worst_hal < 0.72:
        evidence_parts.append(
            f"Worst offender: '{worst_heading['heading_text'][:60]}' has "
            f"{worst_heading['char_distance']} chars of intervening content "
            f"before its answer paragraph (HAL={worst_hal:.2f})."
        )
        if worst_heading["intervening_elements"]:
            evidence_parts.append(
                f"Intervening elements: {', '.join(worst_heading['intervening_elements'][:5])}."
            )

    if worst_hal < 0.30:
        severity = "critical"
    elif worst_hal < 0.55:
        severity = "high"
    elif worst_hal < 0.72:
        severity = "medium"
    else:
        severity = "none"

    return {
        "id": "H-SS2",
        "title": "Heading-to-Answer Semantic Locality",
        "severity": severity,
        "score": round(avg_hal, 4),
        "evidence": " ".join(evidence_parts),
        "suggested_action": {
            "summary": (
                "Position a concise 25-50 word self-contained answer directly under "
                "each heading before presenting secondary promotional elements."
            ),
            "priority": severity if severity != "none" else "low",
        },
    }


# ---------------------------------------------------------------------------
# H-SS3: Fragmented Proposition Split
# ---------------------------------------------------------------------------
def evaluate_ss3_fragmented_proposition(soup: BeautifulSoup) -> dict:
    """Detect logical claims split across multiple DOM container boundaries."""
    main_tag = detect_main_content(soup)
    if not main_tag:
        return {
            "id": "H-SS3",
            "title": "Fragmented Proposition Split",
            "severity": "none",
            "score": 1.0,
            "evidence": "No main content block detected for fragmentation analysis.",
            "suggested_action": {"summary": "N/A", "priority": "low"},
        }

    fragmented = []
    # Look at consecutive sibling block elements
    blocks = main_tag.find_all(["div", "section", "p", "li"], recursive=True)

    for i in range(len(blocks) - 1):
        text_a = blocks[i].get_text(strip=True)
        text_b = blocks[i + 1].get_text(strip=True)

        if not text_a or not text_b:
            continue

        # Heuristic: block A ends without terminal punctuation AND block B starts lowercase
        ends_without_period = not re.search(r"[.!?:;]\s*$", text_a)
        starts_lowercase = text_b and text_b[0].islower()

        # Heuristic: block A ends with a conjunction or colon
        ends_with_connector = bool(
            re.search(r"\b(and|or|but|including|such as|e\.g\.|i\.e\.|:)\s*$", text_a, re.I)
        )

        if (ends_without_period and starts_lowercase) or ends_with_connector:
            fragmented.append(
                f"Split between '{text_a[-50:]}' → '{text_b[:50]}' "
                f"across {blocks[i].name}/{blocks[i+1].name} boundary."
            )

    frag_count = len(fragmented)
    score = max(0.0, 1.0 - frag_count * 0.15)

    if frag_count > 3:
        severity = "high"
    elif frag_count >= 1:
        severity = "medium"
    else:
        severity = "none"

    evidence = f"Detected {frag_count} fragmented propositions across DOM boundaries."
    if fragmented:
        evidence += " " + " ".join(fragmented[:3])

    return {
        "id": "H-SS3",
        "title": "Fragmented Proposition Split",
        "severity": severity,
        "score": round(score, 4),
        "evidence": evidence,
        "suggested_action": {
            "summary": (
                "Ensure each complete claim or factual statement resides within a single "
                "<p> or <li> element so RAG chunkers cannot truncate it mid-sentence."
            ),
            "priority": severity if severity != "none" else "low",
        },
    }


# ---------------------------------------------------------------------------
# Proactive Recommendation Engine
# ---------------------------------------------------------------------------
def proactive_recommendation_generator(mcdr: float, hal: float) -> dict:
    """Always generates at least one proactive optimization, even on PASS pages."""
    recommendations = []

    if mcdr >= 0.50 and hal >= 0.72:
        recommendations.append(
            "Add a 'Key Facts Summary Box' directly under the H1 to boost "
            "RAG chunk retrieval priority by ~40%. This structured summary "
            "gives AI assistants a self-contained answer candidate."
        )
    if mcdr >= 0.70:
        recommendations.append(
            "Consider adding schema.org FAQPage markup to top Q&A sections "
            "for direct LLM snippet extraction."
        )
    if hal < 0.72:
        recommendations.append(
            "Relocate promotional banners and CTAs to AFTER the first "
            "substantive answer paragraph under each heading."
        )
    if mcdr < 0.50:
        recommendations.append(
            "Wrap core content in a <main> landmark and add aria-label "
            "to identify the primary content region for accessibility and AI parsers."
        )

    # Always have at least one
    if not recommendations:
        recommendations.append(
            "Page scores well. Consider adding explicit 'Last Updated' dates "
            "near factual claims to boost temporal relevance scoring."
        )

    return {
        "id": "PROACTIVE-SS",
        "title": "Source Selection Proactive Optimization",
        "severity": "info",
        "evidence": " | ".join(recommendations),
        "suggested_action": {
            "summary": recommendations[0],
            "priority": "low",
        },
    }


# ---------------------------------------------------------------------------
# Main Orchestrator
# ---------------------------------------------------------------------------
def run_source_selection_audit(html_content: str, url: str) -> dict:
    """Run all Source Selection hypothesis checks and return Adobe-schema JSON."""
    soup = BeautifulSoup(html_content, "html.parser")

    execution_warning = None
    if detect_spa_placeholder(soup):
        execution_warning = "JS_RENDER_REQUIRED"

    ss1 = evaluate_ss1_content_density(soup)
    ss2 = evaluate_ss2_heading_locality(soup)
    ss3 = evaluate_ss3_fragmented_proposition(soup)

    mcdr = ss1.get("score", 0.5)
    hal = ss2.get("score", 0.5)

    # Composite Source Selection Score
    score_ss = 0.55 * mcdr + 0.45 * hal

    findings = []
    for f in [ss1, ss2, ss3]:
        if f["severity"] != "none":
            findings.append(f)

    # Always include proactive recommendation
    proactive = proactive_recommendation_generator(mcdr, hal)
    findings.append(proactive)

    report = {
        "audited_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "site": url,
        "score_ss": round(score_ss, 4),
        "summary": {
            "total_findings": len(findings),
            "critical": sum(1 for f in findings if f["severity"] == "critical"),
            "high": sum(1 for f in findings if f["severity"] == "high"),
            "medium": sum(1 for f in findings if f["severity"] == "medium"),
            "low": sum(1 for f in findings if f["severity"] == "low"),
        },
        "findings": findings,
    }

    if execution_warning:
        report["execution_warning"] = execution_warning

    return report


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    target = sys.argv[1] if len(sys.argv) > 1 else "https://www.adobe.com"

    if target.endswith(".html") or os.path.isfile(target):
        with open(target, "r", encoding="utf-8") as f:
            html = f.read()
        label = os.path.basename(target)
    else:
        html = fetch_html(target)
        label = target

    if not html:
        print(json.dumps({"error": f"Failed to retrieve HTML from {target}"}))
        sys.exit(1)

    result = run_source_selection_audit(html, label)
    print(json.dumps(result, indent=2))
