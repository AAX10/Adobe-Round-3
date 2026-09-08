#!/usr/bin/env python3
"""
run_audit.py — Entrypoint: run a full AI discoverability audit and emit a single report.

This is the orchestrator script that composes outputs from crawl-audit,
extractability-audit, and non-text-lockin-audit into the unified report schema
required by the marketplace.

Usage:
    python skills/audit-orchestrator/scripts/run_audit.py --url https://example.com [--output report.json]
    python skills/audit-orchestrator/scripts/run_audit.py --help

Output conforms to the required audit report schema:
{
  "site": "...",
  "audited_at": "...",
  "summary": { "total_findings": N, "critical": N, "high": N, "medium": N, "low": N },
  "findings": [ { "id", "title", "severity", "evidence", "suggested_action" }, ... ]
}
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

# Resolve paths relative to the marketplace root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MARKETPLACE_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
SCRIPTS_DIR = os.path.join(MARKETPLACE_ROOT, "scripts")

DEFAULT_TIMEOUT = 15
MAX_PAGES_TO_AUDIT = 5  # Bound page-level checks


def run_script(script_path: str, args: list, cwd: str = None) -> dict:
    """Run a Python script and capture its JSON output."""
    cmd = [sys.executable, script_path] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=cwd or MARKETPLACE_ROOT,
        )
        if result.returncode in (0, 1) and result.stdout.strip():
            return json.loads(result.stdout)
        else:
            return {"status": "error", "error": result.stderr[:500] if result.stderr else "No output"}
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Script timed out after 120s"}
    except json.JSONDecodeError:
        return {"status": "error", "error": "Invalid JSON output"}
    except FileNotFoundError:
        return {"status": "error", "error": f"Script not found: {script_path}"}
    except Exception as e:
        return {"status": "error", "error": str(e)[:500]}


def extract_findings_from_check(check_result: dict) -> list:
    """Extract findings in the required schema from a single check result."""
    findings = []

    if not check_result or check_result.get("status") not in ("finding",):
        return findings

    check_id = check_result.get("check_id", "UNKNOWN")
    title_map = {
        "A-001": "Crawl-Blocked Important Content",
        "A-002": "Non-Crawlable Navigation Patterns",
        "A-003": "Important URL Retrieval Failures",
        "C-003": "Ambiguous Fact-to-Label Association",
        "F-001": "Image-Only Core Facts Without Text Equivalents",
        "F-002": "Document-Only Critical Information",
        "F-003": "Non-Text Visual/Interactive Fact Lock-In",
    }

    findings.append({
        "id": check_id,
        "title": title_map.get(check_id, check_id),
        "severity": check_result.get("severity", "low"),
        "evidence": check_result.get("reason", "No details available."),
        "suggested_action": check_result.get("suggested_action", {
            "summary": "Review the detailed evidence and apply the recommended fix.",
            "priority": check_result.get("severity", "low"),
        }),
    })

    return findings


def extract_important_pages(base_url: str, timeout: int = DEFAULT_TIMEOUT) -> list:
    """Extract a small set of important pages from the site for page-level checks."""
    # Use the link discovery script to get initial page links
    link_script = os.path.join(SCRIPTS_DIR, "crawlability", "link_discovery_audit.py")
    result = run_script(link_script, ["--url", base_url])

    pages = [base_url]

    if result.get("evidence", {}).get("static_links_found", 0) > 0:
        # Get some sitemap URLs if available
        sitemap_sample = result.get("evidence", {}).get("sitemap_only_urls_sample", [])
        pages.extend(sitemap_sample[:3])

    # Deduplicate and bound
    seen = set()
    unique_pages = []
    for p in pages:
        if p not in seen:
            seen.add(p)
            unique_pages.append(p)
        if len(unique_pages) >= MAX_PAGES_TO_AUDIT:
            break

    return unique_pages


def run_full_audit(base_url: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Run the full orchestrated audit and produce the final report."""
    audit_start = datetime.now(timezone.utc)
    parsed = urlparse(base_url)
    site_domain = parsed.netloc or parsed.path

    all_findings = []

    # ═══════════════════════════════════════════════════════
    # PHASE 1: Crawlability checks (site-level)
    # ═══════════════════════════════════════════════════════

    # A-001: robots.txt audit
    robots_script = os.path.join(SCRIPTS_DIR, "crawlability", "robots_audit.py")
    robots_result = run_script(robots_script, ["--url", base_url, "--timeout", str(timeout)])
    all_findings.extend(extract_findings_from_check(robots_result))

    # A-002: link discovery audit (already run for page extraction, reuse if possible)
    link_script = os.path.join(SCRIPTS_DIR, "crawlability", "link_discovery_audit.py")
    link_result = run_script(link_script, ["--url", base_url, "--timeout", str(timeout)])
    all_findings.extend(extract_findings_from_check(link_result))

    # A-003: URL retrieval audit
    retrieval_script = os.path.join(SCRIPTS_DIR, "crawlability", "url_retrieval_audit.py")
    retrieval_result = run_script(retrieval_script, ["--url", base_url, "--timeout", str(timeout)])
    all_findings.extend(extract_findings_from_check(retrieval_result))

    # ═══════════════════════════════════════════════════════
    # PHASE 2: Extractability checks (page-level)
    # ═══════════════════════════════════════════════════════

    # C-003: Semantic association audit on the main page
    semantic_script = os.path.join(SCRIPTS_DIR, "extractability", "semantic_association_audit.py")
    semantic_result = run_script(semantic_script, ["--url", base_url, "--timeout", str(timeout)])
    all_findings.extend(extract_findings_from_check(semantic_result))

    # ═══════════════════════════════════════════════════════
    # PHASE 3: Non-text lock-in checks (page-level)
    # ═══════════════════════════════════════════════════════

    # F-001: Image fact audit
    image_script = os.path.join(SCRIPTS_DIR, "non_text_lockin", "image_fact_audit.py")
    image_result = run_script(image_script, ["--url", base_url, "--timeout", str(timeout)])
    all_findings.extend(extract_findings_from_check(image_result))

    # F-002: Document fact audit
    doc_script = os.path.join(SCRIPTS_DIR, "non_text_lockin", "document_fact_audit.py")
    doc_result = run_script(doc_script, ["--url", base_url, "--timeout", str(timeout)])
    all_findings.extend(extract_findings_from_check(doc_result))

    # F-003: Visual media audit
    media_script = os.path.join(SCRIPTS_DIR, "non_text_lockin", "visual_media_audit.py")
    media_result = run_script(media_script, ["--url", base_url, "--timeout", str(timeout)])
    all_findings.extend(extract_findings_from_check(media_result))

    # ═══════════════════════════════════════════════════════
    # PHASE 4: Compose final report
    # ═══════════════════════════════════════════════════════

    # Count severities
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in all_findings:
        sev = f.get("severity", "low")
        if sev in severity_counts:
            severity_counts[sev] += 1

    report = {
        "site": site_domain,
        "audited_at": audit_start.isoformat().replace("+00:00", "Z"),
        "summary": {
            "total_findings": len(all_findings),
            "critical": severity_counts["critical"],
            "high": severity_counts["high"],
            "medium": severity_counts["medium"],
            "low": severity_counts["low"],
        },
        "findings": all_findings,
    }

    return report


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run a full AI discoverability audit on a public website. "
            "Composes crawl, extractability, and non-text lock-in checks "
            "into a single audit report."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_audit.py --url https://example.com
  python run_audit.py --url https://example.com --output audit_report.json
        """,
    )
    parser.add_argument("--url", required=True, help="Base URL of the site to audit")
    parser.add_argument("--output", help="Output JSON report file path")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help=f"Per-request timeout in seconds (default: {DEFAULT_TIMEOUT})")

    args = parser.parse_args()

    print(f"Starting AI discoverability audit for {args.url}...", file=sys.stderr)
    report = run_full_audit(args.url, args.timeout)
    print(f"Audit complete. {report['summary']['total_findings']} findings.", file=sys.stderr)

    output_json = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
