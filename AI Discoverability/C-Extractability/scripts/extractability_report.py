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
    if render.get("text", {}).get("significant_delta"):
        sev = "high" if render["text"]["ratio"] > 2.0 else "medium"
        findings.append({
            "id": "C-001",
            "title": "Render-Dependent Factual Content",
            "severity": sev,
            "evidence": f"Text delta: {render['text']['delta']} chars (ratio: {render['text']['ratio']}x)",
            "suggested_action": {"summary": "Server-render critical content into initial HTML", "priority": sev},
        })
        severity_counts[sev] += 1

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


def main():
    parser = argparse.ArgumentParser(description="Aggregate extractability audit results.")
    parser.add_argument("--render", help="Path to render comparison JSON")
    parser.add_argument("--schema", help="Path to structured data comparison JSON")
    parser.add_argument("--semantic", help="Path to semantic association audit JSON")
    parser.add_argument("--output", help="Output report JSON path")

    args = parser.parse_args()

    render = load_json(args.render) if args.render else {}
    schema = load_json(args.schema) if args.schema else {}
    semantic = load_json(args.semantic) if args.semantic else {}

    report = aggregate_report(render, schema, semantic)

    output = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output)


if __name__ == "__main__":
    main()
