"""
audit.py — Master Orchestrator for the Brand AI Readiness Audit.

Single entrypoint that runs all mechanism auditors (A, B, C, D, F)
against a target URL and produces one unified JSON report.

Usage:
    python audit.py <url>
    python audit.py https://www.adobe.com
    python audit.py https://stripe.com/pricing --mechanisms B D
"""

import os
import sys
import json
import datetime
import argparse
import importlib.util
import io



# Resolve to repo root (this script lives at skills/master-orchestrator/scripts/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# ── Mechanism Registry ──────────────────────────────────────────────────────
# Each entry maps a mechanism ID to its script path and entry function.
MECHANISMS = {
    "B": {
        "name": "Source Selection & Quote Feasibility",
        "script": os.path.join(BASE_DIR, "skills", "B-Source-Selection",
                               "skills", "audit-orchestrator", "scripts", "orchestrate.py"),
        "function": "run_orchestrated_audit",
    },
    "D": {
        "name": "Entity Resolution",
        "script": os.path.join(BASE_DIR, "skills", "D-Entity-Resolution",
                               "scripts", "audit_mechanism_d.py"),
        "function": "run_audit",
    },
}

# Mechanisms A, C, F use subprocess since they have different calling conventions
SUBPROCESS_MECHANISMS = {
    "A": {
        "name": "Crawlability",
        "script": os.path.join(BASE_DIR, "skills", "A-Crawlability",
                               "scripts", "crawlability_report.py"),
    },
    "C": {
        "name": "Extractability",
        "script": os.path.join(BASE_DIR, "skills", "C-Extractability",
                               "scripts", "extractability_report.py"),
    },
    "E": {
        "name": "Personalization",
        "script": os.path.join(BASE_DIR, "skills", "E-Personalization", "entrypoint.py"),
    },
    "F": {
        "name": "Non-Text Lock-In",
        "script": os.path.join(BASE_DIR, "skills", "F-Non-Text-Lock-In",
                               "scripts", "non_text_report.py"),
    },
}



def load_module(script_path, module_name):
    """Dynamically load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)

    # Add the script's directory to sys.path so its local imports work
    script_dir = os.path.dirname(script_path)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    spec.loader.exec_module(module)
    return module


def run_mechanism_import(mech_id, info, target):
    """Run a mechanism via direct Python import."""
    script = info["script"]
    if not os.path.exists(script):
        return {
            "mechanism": mech_id,
            "name": info["name"],
            "status": "SKIPPED",
            "reason": f"Script not found: {os.path.basename(script)}",
        }

    try:
        module = load_module(script, f"mechanism_{mech_id}")
        func = getattr(module, info["function"])
        result = func(target)
        return {
            "mechanism": mech_id,
            "name": info["name"],
            "status": "OK",
            "result": result,
        }
    except Exception as e:
        return {
            "mechanism": mech_id,
            "name": info["name"],
            "status": "ERROR",
            "error": str(e),
        }


def run_mechanism_subprocess(mech_id, info, target):
    """Run a mechanism via subprocess and capture JSON output."""
    import subprocess

    script = info["script"]
    if not os.path.exists(script):
        return {
            "mechanism": mech_id,
            "name": info["name"],
            "status": "SKIPPED",
            "reason": f"Script not found: {os.path.basename(script)}",
        }

    try:
        result = subprocess.run(
            [sys.executable, script, target],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=os.path.dirname(script),
        )
        if result.returncode == 0 and result.stdout.strip():
            try:
                parsed = json.loads(result.stdout)
                return {
                    "mechanism": mech_id,
                    "name": info["name"],
                    "status": "OK",
                    "result": parsed,
                }
            except json.JSONDecodeError:
                return {
                    "mechanism": mech_id,
                    "name": info["name"],
                    "status": "OK",
                    "result": {"raw_output": result.stdout[:2000]},
                }
        else:
            return {
                "mechanism": mech_id,
                "name": info["name"],
                "status": "ERROR",
                "error": result.stderr[:500] if result.stderr else "No output",
            }
    except subprocess.TimeoutExpired:
        return {
            "mechanism": mech_id,
            "name": info["name"],
            "status": "TIMEOUT",
            "error": "Execution exceeded 120s timeout",
        }
    except Exception as e:
        return {
            "mechanism": mech_id,
            "name": info["name"],
            "status": "ERROR",
            "error": str(e),
        }


def aggregate_findings(mechanism_results):
    """Merge all findings from mechanism results into a unified list."""
    all_findings = []
    for mr in mechanism_results:
        if mr.get("status") != "OK":
            continue
        result = mr.get("result") or {}

        # Handle different output formats from different mechanisms
        findings = result.get("findings", [])
        evaluations = result.get("evaluations", [])

        for f in findings:
            f["mechanism"] = mr["mechanism"]
            all_findings.append(f)

        for ev in evaluations:
            ev["mechanism"] = mr["mechanism"]
            all_findings.append(ev)

    return all_findings


def compute_severity_summary(findings):
    """Count findings by severity."""
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        sev = f.get("severity", "info")
        if sev in counts:
            counts[sev] += 1
    counts["total_findings"] = sum(counts.values())
    return counts


def main():
    parser = argparse.ArgumentParser(
        description="Brand AI Readiness Audit — Master Orchestrator"
    )
    parser.add_argument("target", help="URL or local HTML filepath to audit")
    parser.add_argument(
        "--mechanisms",
        nargs="+",
        default=None,
        help="Specific mechanisms to run (e.g., B D). Default: all available.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path for JSON report. Default: stdout.",
    )
    args = parser.parse_args()

    target = args.target
    requested = set(args.mechanisms) if args.mechanisms else None

    print(f"{'=' * 60}", file=sys.stderr)
    print(f"  Brand AI Readiness Audit", file=sys.stderr)
    print(f"  Target: {target}", file=sys.stderr)
    print(f"{'=' * 60}", file=sys.stderr)

    mechanism_results = []

    # Run importable mechanisms (B, D)
    for mech_id, info in MECHANISMS.items():
        if requested and mech_id not in requested:
            continue
        print(f"\n  ▶ [{mech_id}] {info['name']}...", file=sys.stderr)
        result = run_mechanism_import(mech_id, info, target)
        print(f"    Status: {result['status']}", file=sys.stderr)
        mechanism_results.append(result)

    # Run subprocess mechanisms (A, C, F)
    for mech_id, info in SUBPROCESS_MECHANISMS.items():
        if requested and mech_id not in requested:
            continue
        print(f"\n  ▶ [{mech_id}] {info['name']}...", file=sys.stderr)
        result = run_mechanism_subprocess(mech_id, info, target)
        print(f"    Status: {result['status']}", file=sys.stderr)
        mechanism_results.append(result)

    # Aggregate
    all_findings = aggregate_findings(mechanism_results)
    summary = compute_severity_summary(all_findings)

    # Build final report
    report = {
        "site": target,
        "audited_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "summary": summary,
        "findings": all_findings,
    }

    # Output
    report_json = json.dumps(report, indent=2, default=str)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report_json)
        print(f"\n  📄 Report written to: {args.output}", file=sys.stderr)
    else:
        print(report_json)

    print(f"\n{'=' * 60}", file=sys.stderr)
    print(f"  SUMMARY: {summary['total_findings']} findings", file=sys.stderr)
    print(f"  🔴 Critical: {summary['critical']}  🟠 High: {summary['high']}  "
          f"🟡 Medium: {summary['medium']}  🟢 Low: {summary['low']}", file=sys.stderr)
    print(f"{'=' * 60}", file=sys.stderr)


if __name__ == "__main__":
    main()
