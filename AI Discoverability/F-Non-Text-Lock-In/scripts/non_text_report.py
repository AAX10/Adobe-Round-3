#!/usr/bin/env python3
"""
non_text_report.py — Aggregate non-text lock-in audit results into a unified report.

Usage:
    python non_text_report.py --images f001.json --docs f002.json --media f003.json [--output report.json]
"""

import argparse
import json
import sys
from datetime import datetime, timezone


def load_json(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load {path}: {e}", file=sys.stderr)
        return {}


def aggregate_report(images: dict, docs: dict, media: dict) -> dict:
    timestamp = datetime.now(timezone.utc).isoformat()
    findings = []
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

    for check_data in [images, docs, media]:
        if not check_data or check_data.get("status") != "finding":
            continue
        sev = check_data.get("severity", "low")
        findings.append({
            "id": check_data.get("check_id"),
            "title": {
                "F-001": "Image-Only Core Facts",
                "F-002": "Document-Only Critical Information",
                "F-003": "Non-Text Visual/Interactive Fact Lock-In",
            }.get(check_data.get("check_id", ""), "Non-Text Lock-In"),
            "severity": sev,
            "evidence": check_data.get("reason", ""),
            "suggested_action": check_data.get("suggested_action"),
        })
        if sev in severity_counts:
            severity_counts[sev] += 1

    severity_order = ["critical", "high", "medium", "low", "info"]
    overall = None
    for s in severity_order:
        if severity_counts.get(s, 0) > 0:
            overall = s
            break

    return {
        "report_type": "non_text_lockin",
        "mechanism": "lock-in",
        "timestamp": timestamp,
        "site": images.get("site") or docs.get("site") or media.get("site", "unknown"),
        "summary": {
            "total_findings": len(findings),
            "overall_severity": overall,
            "severity_counts": severity_counts,
        },
        "findings": findings,
    }


def main():
    parser = argparse.ArgumentParser(description="Aggregate non-text lock-in results.")
    parser.add_argument("--images", help="Path to F-001 image audit JSON")
    parser.add_argument("--docs", help="Path to F-002 document audit JSON")
    parser.add_argument("--media", help="Path to F-003 visual media audit JSON")
    parser.add_argument("--output", help="Output report JSON path")

    args = parser.parse_args()

    images = load_json(args.images) if args.images else {}
    docs = load_json(args.docs) if args.docs else {}
    media = load_json(args.media) if args.media else {}

    report = aggregate_report(images, docs, media)
    output = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output)


if __name__ == "__main__":
    main()
