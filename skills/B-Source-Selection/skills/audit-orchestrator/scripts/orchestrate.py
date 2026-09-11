"""
orchestrate.py — Master Audit Orchestrator for Mechanism B.

Aggregates Source Selection and Quote Feasibility sub-auditors,
applies severity escalation, deduplication, and composite scoring.

Usage:
    python orchestrate.py <url_or_filepath>
"""

import os
import sys
import json
import datetime

# ── Dynamic imports from sibling skill directories ──────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SS_SCRIPTS = os.path.join(BASE_DIR, "source-selection-auditor", "scripts")
QF_SCRIPTS = os.path.join(BASE_DIR, "quote-feasibility-auditor", "scripts")

sys.path.insert(0, SS_SCRIPTS)
sys.path.insert(0, QF_SCRIPTS)

from evaluate_source_selection import run_source_selection_audit
from utils_html import fetch_html
from evaluate_quote_feasibility import run_quote_feasibility_audit


SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0, "none": -1}


def escalate_severity(findings: list) -> list:
    """If both H-SS2 AND H-QF1 fire, escalate both to at minimum HIGH."""
    ss2_present = any(f.get("id") == "H-SS2" for f in findings)
    qf1_present = any(f.get("id") == "H-QF1" for f in findings)

    if ss2_present and qf1_present:
        for f in findings:
            if f.get("id") in ("H-SS2", "H-QF1"):
                rank = SEVERITY_RANK.get(f.get("severity", "info"), 0)
                if rank < SEVERITY_RANK["high"]:
                    f["severity"] = "high"
                    f["evidence"] = (
                        f.get("evidence", "")
                        + " [ESCALATED: H-SS2 + H-QF1 co-occurrence triggers mandatory HIGH floor.]"
                    )
    return findings


def deduplicate_findings(findings: list) -> list:
    """Keep only the highest-severity finding per hypothesis ID."""
    best = {}
    non_dedup = []
    for f in findings:
        fid = f.get("id", "")
        if not fid or fid.startswith("PROACTIVE"):
            non_dedup.append(f)
            continue
        rank = SEVERITY_RANK.get(f.get("severity", "info"), 0)
        if fid not in best or rank > SEVERITY_RANK.get(best[fid].get("severity", "info"), 0):
            best[fid] = f
    return list(best.values()) + non_dedup


def map_score_to_severity(score: float) -> str:
    if score < 0.40:
        return "critical"
    elif score < 0.65:
        return "high"
    elif score < 0.82:
        return "medium"
    else:
        return "pass"


def normalize_qf_findings(qf_result: dict) -> list:
    """Convert the QF evaluator's output format to match Adobe schema."""
    findings = []
    for ev in qf_result.get("evaluations", []):
        sev = ev.get("severity", "none")
        # Skip fully passing checks — don't surface noise
        if sev == "none":
            continue
        metric = ev.get("metric_value", 1.0)
        if sev == "low" and (isinstance(metric, float) and metric >= 0.82):
            continue

        evidence_data = ev.get("evidence", [])
        if isinstance(evidence_data, list):
            clean_evidence = [" ".join(str(e).split()) for e in evidence_data[:3]]
            evidence_str = " | ".join(e[:120] + "..." if len(e) > 120 else e for e in clean_evidence if e)
        else:
            evidence_str = str(evidence_data)

        # Fallback evidence if empty
        if not evidence_str:
            if ev.get("id") == "H-QF4":
                evidence_str = "No <th> or <caption> tags found in tabular data."
            elif ev.get("id") == "H-QF5":
                evidence_str = "Main content area lacks dense paragraph structures."
            else:
                evidence_str = f"Failed check threshold (Value: {ev.get('metric_value')})"

        suggestions = {
            "H-QF1": "Add semantic table elements (<th>, <caption>) to improve machine-readability of tabular data.",
            "H-QF2": "Reduce complex visual layouts in favor of linear document flows where possible.",
            "H-QF3": "Provide explicit labels and context for standalone numbers so AI extractors understand what they represent.",
            "H-QF4": "Use complete HTML table markup (<th>, <thead>) instead of CSS grids for tabular data to ensure machine parsers can map columns correctly.",
            "H-QF5": "Consolidate core claims into dense summary blocks and reduce filler text to improve RAG chunk signal-to-noise ratio."
        }
        
        suggested_summary = suggestions.get(ev.get("id"), f"Address {ev.get('id', '')} finding to improve quote feasibility.")

        finding_obj = {
            "id": ev.get("id", ""),
            "title": ev.get("name", ev.get("id", "")),
            "severity": sev,
            "evidence": evidence_str,
            "suggested_action": {
                "summary": suggested_summary,
                "priority": sev,
            },
        }
        findings.append(finding_obj)

    # Add proactive recommendations from QF
    for rec in qf_result.get("recommendations", []):
        findings.append({
            "id": "H-QF-INFO",
            "title": "Quote Feasibility Proactive Optimization",
            "severity": "low",
            "evidence": "Missed proactive optimization opportunity.",
            "suggested_action": {"summary": rec, "priority": "low"},
        })

    return findings


def run_orchestrated_audit(target: str):
    """Full orchestrated audit pipeline."""
    # ── Fetch HTML once, share across sub-auditors ──
    if target.endswith(".html") or os.path.isfile(target):
        with open(target, "r", encoding="utf-8") as f:
            html = f.read()
        label = os.path.basename(target)
    else:
        html = fetch_html(target)
        label = target

    if not html:
        return {"error": f"Failed to retrieve HTML from {target}"}

    # ── Run Sub-Auditors ──
    ss_result = run_source_selection_audit(html, label)
    qf_result = run_quote_feasibility_audit(target, is_url=target.startswith("http"))

    # ── Collect & Normalize Findings ──
    ss_findings = ss_result.get("findings", [])
    qf_findings = normalize_qf_findings(qf_result)
    all_findings = ss_findings + qf_findings

    # ── Severity Escalation ──
    all_findings = escalate_severity(all_findings)

    # ── Deduplication ──
    all_findings = deduplicate_findings(all_findings)

    # ── Composite Score ──
    score_ss = ss_result.get("score_ss", 0.5)
    score_qf = qf_result.get("score_qf", 0.5)
    score_composite = 0.50 * score_ss + 0.50 * score_qf
    overall_severity = map_score_to_severity(score_composite)

    # ── Global Count Synchronization ──
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in all_findings:
        sev = f.get("severity", "info")
        if sev in severity_counts:
            severity_counts[sev] += 1

    # ── Build Adobe-Schema Report ──
    report = {
        "audited_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "site": label,
        "composite_score": round(score_composite, 4),
        "overall_severity": overall_severity,
        "sub_scores": {
            "source_selection": round(score_ss, 4),
            "quote_feasibility": round(score_qf, 4),
        },
        "summary": {
            "total_findings": len(all_findings),
            **severity_counts,
        },
        "findings": all_findings,
    }

    # ── Propagate SPA warning ──
    if ss_result.get("execution_warning"):
        report["execution_warning"] = ss_result["execution_warning"]

    # ── Write to outputs/ ──
    output_dir = os.path.join(BASE_DIR, "outputs")
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "benchmark_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    import io
    

    target = sys.argv[1] if len(sys.argv) > 1 else "https://www.adobe.com"
    result = run_orchestrated_audit(target)
    print(json.dumps(result, indent=2))
