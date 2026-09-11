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


def run_sub_script(script_name, target_url):
    import subprocess
    import os
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    try:
        res = subprocess.run([sys.executable, script_path, "--url", target_url], capture_output=True, text=True, timeout=60)
        if res.returncode == 0 and res.stdout.strip():
            # Try to parse only the JSON part (skipping any plain text logs)
            try:
                # Find the first { character
                start_idx = res.stdout.find('{')
                if start_idx != -1:
                    return json.loads(res.stdout[start_idx:])
            except json.JSONDecodeError:
                pass
    except Exception:
        pass
    return {}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Target URL to audit")
    args = parser.parse_args()

    robots = run_sub_script("robots_audit.py", args.url)
    links = run_sub_script("link_discovery_audit.py", args.url)
    retrieval = run_sub_script("url_retrieval_audit.py", args.url)

    report = aggregate_report(robots, links, retrieval)
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
