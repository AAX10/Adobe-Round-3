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


def run_sub_script(script_name, target_url):
    import subprocess
    import os
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    try:
        res = subprocess.run([sys.executable, script_path, target_url], capture_output=True, text=True, timeout=60)
        if res.returncode == 0 and res.stdout.strip():
            try:
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

    images = run_sub_script("image_fact_audit.py", args.url)
    docs = run_sub_script("document_fact_audit.py", args.url)
    media = run_sub_script("visual_media_audit.py", args.url)

    report = aggregate_report(images, docs, media)
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
