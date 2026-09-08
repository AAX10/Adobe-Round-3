#!/usr/bin/env python3
"""
crawlability_report.py — Aggregate crawlability audit results into a unified report.

Combines outputs from robots_audit, link_discovery_audit, and url_retrieval_audit
into a single structured crawlability assessment.

Usage:
    python crawlability_report.py --robots robots.json --links links.json --retrieval retrieval.json [--output report.json]
    python crawlability_report.py --help
"""

import argparse
import json
import sys
from datetime import datetime, timezone


def load_json(path: str) -> dict:
    """Load a JSON file, returning empty dict on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load {path}: {e}", file=sys.stderr)
        return {}


def aggregate_report(robots: dict, links: dict, retrieval: dict) -> dict:
    """Aggregate individual check results into a unified report."""
    timestamp = datetime.now(timezone.utc).isoformat()

    checks = []
    findings = []
    total_findings = 0
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

    for check_data, check_name in [(robots, "A-001"), (links, "A-002"), (retrieval, "A-003")]:
        if not check_data:
            checks.append({"check_id": check_name, "status": "skipped"})
            continue

        status = check_data.get("status", "unknown")
        severity = check_data.get("severity")

        checks.append({
            "check_id": check_data.get("check_id", check_name),
            "status": status,
            "severity": severity,
            "reason": check_data.get("reason", ""),
        })

        if status == "finding" and severity:
            total_findings += 1
            if severity in severity_counts:
                severity_counts[severity] += 1

            findings.append({
                "id": check_data.get("check_id", check_name),
                "title": {
                    "A-001": "Crawl-Blocked Important Content",
                    "A-002": "Non-Crawlable Navigation Patterns",
                    "A-003": "Important URL Retrieval Failures",
                }.get(check_name, check_name),
                "severity": severity,
                "evidence": check_data.get("reason", ""),
                "suggested_action": check_data.get("suggested_action"),
            })

    # Overall severity = worst individual severity
    severity_order = ["critical", "high", "medium", "low", "info"]
    overall_severity = None
    for sev in severity_order:
        if severity_counts.get(sev, 0) > 0:
            overall_severity = sev
            break

    return {
        "report_type": "crawlability",
        "mechanism": "crawl",
        "timestamp": timestamp,
        "site": robots.get("site") or links.get("site") or retrieval.get("site", "unknown"),
        "summary": {
            "total_checks": len(checks),
            "total_findings": total_findings,
            "overall_severity": overall_severity,
            "severity_counts": severity_counts,
        },
        "checks": checks,
        "findings": findings,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate crawlability audit results into a unified report.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python crawlability_report.py --robots a001.json --links a002.json --retrieval a003.json
  python crawlability_report.py --robots a001.json --output crawl_report.json
        """,
    )
    parser.add_argument("--robots", help="Path to A-001 robots audit JSON")
    parser.add_argument("--links", help="Path to A-002 link discovery audit JSON")
    parser.add_argument("--retrieval", help="Path to A-003 URL retrieval audit JSON")
    parser.add_argument("--output", help="Output report JSON file path")

    args = parser.parse_args()

    robots = load_json(args.robots) if args.robots else {}
    links = load_json(args.links) if args.links else {}
    retrieval = load_json(args.retrieval) if args.retrieval else {}

    report = aggregate_report(robots, links, retrieval)

    output_json = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
