"""
test_runner.py — Validates Mechanism B audit pipeline against mock fixtures.

Runs the orchestrator against all .html files in tests/mock_pages/
and validates expected findings per fixture. Optionally runs live URLs
from benchmark_urls.json.

Usage:
    python test_runner.py           # Mock pages only
    python test_runner.py --live    # Mock pages + live URLs
"""

import os
import sys
import json
import datetime
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORCHESTRATOR_DIR = os.path.join(BASE_DIR, "skills", "audit-orchestrator", "scripts")
sys.path.insert(0, ORCHESTRATOR_DIR)

from orchestrate import run_orchestrated_audit


MOCK_EXPECTATIONS = {
    "perfect_page.html": {
        "check_name": "Perfect Page — zero critical/high",
        "assertions": [
            ("composite_score >= 0.82", lambda r: r.get("composite_score", 0) >= 0.82),
            ("0 critical findings", lambda r: r.get("summary", {}).get("critical", 99) == 0),
            ("0 high findings", lambda r: r.get("summary", {}).get("high", 99) == 0),
            ("has proactive recs", lambda r: any(f.get("id", "").startswith("PROACTIVE") for f in r.get("findings", []))),
        ],
    },
    "severed_qualifiers.html": {
        "check_name": "Severed Qualifiers — H-QF2 or H-QF3 fires",
        "assertions": [
            ("H-QF2 or H-QF3 present", lambda r: any(
                f.get("id") in ("H-QF2", "H-QF3") and f.get("severity") in ("medium", "high", "critical")
                for f in r.get("findings", [])
            )),
        ],
    },
    "noisy_chrome.html": {
        "check_name": "Noisy Chrome — H-SS1 critical or high",
        "assertions": [
            ("H-SS1 fires critical/high", lambda r: any(
                f.get("id") == "H-SS1" and f.get("severity") in ("critical", "high")
                for f in r.get("findings", [])
            )),
        ],
    },
    "anaphora_heavy.html": {
        "check_name": "Anaphora Heavy — H-QF1 fires",
        "assertions": [
            ("H-QF1 fires high or critical", lambda r: any(
                f.get("id") == "H-QF1" and f.get("severity") in ("high", "critical")
                for f in r.get("findings", [])
            )),
        ],
    },
    "spa_placeholder.html": {
        "check_name": "SPA Placeholder — execution_warning present",
        "assertions": [
            ("JS_RENDER_REQUIRED warning", lambda r: r.get("execution_warning") == "JS_RENDER_REQUIRED"),
        ],
    },
}


def run_mock_tests():
    """Run orchestrator against all mock pages and validate expectations."""
    mock_dir = os.path.join(BASE_DIR, "tests", "mock_pages")
    results = []
    total_pass = 0
    total_fail = 0

    print("=" * 70)
    print("  MECHANISM B — MOCK PAGE TEST SUITE")
    print("=" * 70)

    for filename, spec in MOCK_EXPECTATIONS.items():
        filepath = os.path.join(mock_dir, filename)
        if not os.path.exists(filepath):
            print(f"\n  ❌ SKIP  {filename} — file not found")
            total_fail += 1
            results.append({"file": filename, "status": "SKIP", "reason": "File not found"})
            continue

        print(f"\n  ▶ Testing: {filename} ({spec['check_name']})")
        try:
            report = run_orchestrated_audit(filepath)
        except Exception as e:
            print(f"    ❌ CRASH: {e}")
            total_fail += 1
            results.append({"file": filename, "status": "CRASH", "error": str(e)})
            continue

        file_pass = True
        for desc, assertion_fn in spec["assertions"]:
            passed = assertion_fn(report)
            icon = "✅" if passed else "❌"
            print(f"    {icon} {desc}")
            if not passed:
                file_pass = False

        # Schema compliance checks (always run)
        schema_checks = [
            ("has audited_at", "audited_at" in report),
            ("has site", "site" in report),
            ("has summary", "summary" in report),
            ("has findings list", isinstance(report.get("findings"), list)),
            ("summary has total_findings", "total_findings" in report.get("summary", {})),
        ]
        for desc, passed in schema_checks:
            if not passed:
                print(f"    ❌ SCHEMA: {desc}")
                file_pass = False

        if file_pass:
            total_pass += 1
        else:
            total_fail += 1

        results.append({
            "file": filename,
            "status": "PASS" if file_pass else "FAIL",
            "composite_score": report.get("composite_score"),
            "severity": report.get("overall_severity"),
            "findings_count": report.get("summary", {}).get("total_findings", 0),
        })

    print("\n" + "=" * 70)
    print(f"  RESULTS: {total_pass} PASS / {total_fail} FAIL / {total_pass + total_fail} TOTAL")
    print("=" * 70)

    return results


def run_live_tests():
    """Run orchestrator against live benchmark URLs."""
    urls_path = os.path.join(BASE_DIR, "tests", "benchmark_urls.json")
    if not os.path.exists(urls_path):
        print("\n  ⚠ No benchmark_urls.json found, skipping live tests.")
        return []

    with open(urls_path, "r") as f:
        benchmarks = json.load(f)

    results = []
    print("\n" + "=" * 70)
    print("  MECHANISM B — LIVE BENCHMARK SUITE")
    print("=" * 70)

    for entry in benchmarks:
        url = entry["url"]
        domain = entry.get("domain", "Unknown")
        print(f"\n  ▶ [{domain}] {url}")

        try:
            report = run_orchestrated_audit(url)
            status = "OK"
            print(f"    Score: {report.get('composite_score', 'N/A')} | "
                  f"Severity: {report.get('overall_severity', 'N/A')} | "
                  f"Findings: {report.get('summary', {}).get('total_findings', 0)}")
        except Exception as e:
            status = "ERROR"
            report = {"error": str(e)}
            print(f"    ❌ ERROR: {e}")

        results.append({
            "url": url,
            "domain": domain,
            "status": status,
            "composite_score": report.get("composite_score"),
            "severity": report.get("overall_severity"),
            "execution_warning": report.get("execution_warning"),
        })

    return results


def main():
    run_live = "--live" in sys.argv

    mock_results = run_mock_tests()

    live_results = []
    if run_live:
        live_results = run_live_tests()

    # Write consolidated report
    output_dir = os.path.join(BASE_DIR, "outputs")
    os.makedirs(output_dir, exist_ok=True)

    consolidated = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "mock_tests": mock_results,
        "live_benchmarks": live_results,
    }

    out_path = os.path.join(output_dir, "benchmark_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(consolidated, f, indent=2)

    print(f"\n  📄 Full report written to: {out_path}")


if __name__ == "__main__":
    main()
