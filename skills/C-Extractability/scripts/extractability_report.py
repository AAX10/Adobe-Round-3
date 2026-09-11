#!/usr/bin/env python3
"""
extractability_report.py — Aggregate extractability audit results into a unified report.

Combines outputs from render_compare, structured_data_compare, semantic_association_audit,
and fact_inventory into a single extractability assessment.

Usage:
    python extractability_report.py --render render.json --schema schema.json --semantic semantic.json [--output report.json]
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


def aggregate_report(render: dict, schema: dict, semantic: dict) -> dict:
    timestamp = datetime.now(timezone.utc).isoformat()
    findings = []
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

    # C-001: Render-dependent factual content
    if "findings" in render:
        for finding in render["findings"]:
            if finding["id"] == "C-001":
                findings.append(finding)
                severity_counts[finding["severity"]] += 1

    # C-002: Render-dependent structural metadata
    if schema.get("classification") in ("semantic_loss", "information_loss"):
        sev = "high" if schema["classification"] == "information_loss" else "medium"
        findings.append({
            "id": "C-002",
            "title": "Render-Dependent Structural Metadata",
            "severity": sev,
            "evidence": f"Render-only relevant schemas: {schema.get('render_only_relevant', [])}. Classification: {schema['classification']}",
            "suggested_action": {"summary": "Server-render JSON-LD into initial HTML response", "priority": sev},
        })
        severity_counts[sev] += 1

    # C-003: Ambiguous fact-to-label association
    if semantic.get("status") == "finding":
        sev = semantic.get("severity", "low")
        findings.append({
            "id": "C-003",
            "title": "Ambiguous Fact-to-Label Association",
            "severity": sev,
            "evidence": semantic.get("reason", ""),
            "suggested_action": semantic.get("suggested_action"),
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
        "report_type": "extractability",
        "mechanism": "read/extract",
        "timestamp": timestamp,
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

    render = run_sub_script("check_render_factual_content.py", args.url)
    schema = run_sub_script("structured_data_compare.py", args.url)
    semantic = run_sub_script("semantic_association_audit.py", args.url)

    report = aggregate_report(render, schema, semantic)
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
