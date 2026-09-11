import sys
import json
import datetime
import subprocess
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_master_audit.py <URL>")
        sys.exit(1)
        
    target = sys.argv[1]
    all_findings = []
    
    # 1. Run Node Engagement Audit
    node_script = os.path.join(BASE_DIR, "skills", "engagement-audit-orchestrator", "scripts", "run_audit.js")
    try:
        env = os.environ.copy()
        env["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"
        res = subprocess.run(["node", node_script, target], capture_output=True, text=True, encoding="utf-8", check=True, env=env)
        node_data = json.loads(res.stdout)
        
        # Heuristic Genre Filtering based on Engagement Orchestrator SKILL.md rules
        bme = node_data.get("business_model_evidence", {})
        excerpt = bme.get("homepage_excerpt", "").lower()
        signals = bme.get("genre_signals", {})
        
        # Decide which categories to include based on signals and excerpt
        include_conversion = signals.get("ecommerce", 0) > 0 or signals.get("saas", 0) > 0 or "cart" in excerpt or "pricing" in excerpt
        include_retention = signals.get("news", 0) > 0 or signals.get("community", 0) > 0 or "article" in excerpt or "post" in excerpt or "directory" in excerpt or "points by" in excerpt
        include_local = signals.get("food", 0) > 0 or "contact us" in excerpt or "booking" in excerpt or "appointment" in excerpt

        # Fallback if everything is 0 or unclassified (like indianonline.in)
        if not include_conversion and not include_retention and not include_local:
            include_retention = True
            include_local = True

        e_count = 1
        for category, checks in node_data.get('checks', {}).items():
            if category == "conversion_friction" and not include_conversion:
                continue
            if category == "retention_content" and not include_retention:
                continue
            if category == "local_trust_leads" and not include_local:
                continue
                
            for check in checks:
                finding = {
                    "id": f"E-{e_count:03d}",
                    "title": check.get("title", ""),
                    "severity": check.get("severity", "low"),
                    "evidence": check.get("evidence", ""),
                    "suggested_action": check.get("suggested_action", {})
                }
                # Ensure severity isn't info, map to low for schema compliance
                if finding["severity"] == "info":
                    finding["severity"] = "low"
                all_findings.append(finding)
                e_count += 1
    except Exception as e:
        print(f"Engagement audit failed: {e}", file=sys.stderr)

    # 2. Run Discoverability Audits
    python_script = os.path.join(BASE_DIR, "skills", "master-orchestrator", "scripts", "run_discoverability_audit.py")
    try:
        res = subprocess.run(["python", python_script, target, "--output", "temp_py_out.json"], capture_output=True, text=True, encoding="utf-8", check=True)
        with open("temp_py_out.json", "r", encoding="utf-8") as f:
            py_data = json.load(f)
            
        for f in py_data.get("findings", []):
            if "score" in f:
                del f["score"]
            all_findings.append(f)
            
        if os.path.exists("temp_py_out.json"):
            os.remove("temp_py_out.json")
    except Exception as e:
        print(f"Discoverability audit failed: {e}", file=sys.stderr)
        
    # Recalculate summary
    summary = {"total_findings": len(all_findings), "critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in all_findings:
        sev = f.get("severity", "low")
        if sev in summary:
            summary[sev] += 1

    # Build proactive suggestions dynamically from what was actually found
    proactive_suggestions = []

    # Always: the rendering-dependent gap recommendation (SKILL.md requires at least one naming not_evaluated)
    proactive_suggestions.append({
        "summary": "This audit could not evaluate mobile tap-target sizing, true above-the-fold element count, computed-style sticky-CTA behavior, or live console errors (no browser rendering is used in this submission). Recommend a Lighthouse mobile pass or manual device testing to cover this rendering-dependent gap.",
        "priority": "medium"
    })

    # Dynamic: derive suggestions from what PASSED (no findings) and what FAILED
    finding_ids = {f.get("id") for f in all_findings}
    finding_mechs = {f.get("mechanism") for f in all_findings if f.get("mechanism")}
    severities = [f.get("severity") for f in all_findings]

    # If entity resolution failed, suggest specific fix using actual evidence
    d1 = next((f for f in all_findings if f.get("id") == "H-D1"), None)
    if d1:
        proactive_suggestions.append({
            "summary": f"Site is missing Organization JSON-LD ({d1.get('evidence', '')}). Adding a structured identity block with @id, sameAs, and contactPoint would immediately resolve the highest-impact discoverability gap found.",
            "priority": "high"
        })

    # If mechanism B found issues but C/E/F all passed, note the strength and suggest building on it
    clean_mechs = {"A", "B", "C", "D", "E", "F"} - finding_mechs
    if clean_mechs:
        clean_names = {
            "A": "Crawlability", "B": "Source Selection", "C": "Extractability",
            "D": "Entity Resolution", "E": "Personalization", "F": "Non-Text Lock-In"
        }
        clean_list = ", ".join(clean_names.get(m, m) for m in sorted(clean_mechs) if m in clean_names)
        if clean_list:
            proactive_suggestions.append({
                "summary": f"Mechanisms with no issues detected: {clean_list}. These are strengths to maintain — consider adding structured data enrichment (FAQPage, HowTo) to further capitalize on the clean extraction pipeline.",
                "priority": "low"
            })

    # If high-severity findings dominate, suggest prioritization
    high_count = severities.count("high") + severities.count("critical")
    if high_count >= 3:
        top_highs = [f.get("title", "") for f in all_findings if f.get("severity") in ("high", "critical")][:3]
        proactive_suggestions.append({
            "summary": f"This site has {high_count} high/critical findings. Recommended fix priority: {'; '.join(top_highs)}.",
            "priority": "high"
        })

    # Fixed coverage gaps — always the same 4 rendering-dependent checks
    coverage_gaps = [
        {"check": "mobile_tap_targets", "reason": "Requires rendering a real viewport; this submission uses no browser-automation framework by design."},
        {"check": "above_fold_node_count_true_viewport", "reason": "Requires rendering a real viewport; this submission uses no browser-automation framework by design."},
        {"check": "sticky_cta_computed_style", "reason": "Requires rendering a real viewport; this submission uses no browser-automation framework by design."},
        {"check": "console_errors", "reason": "Requires rendering a real viewport; this submission uses no browser-automation framework by design."}
    ]

    report = {
        "site": target,
        "audited_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scope": "full-audit",
        "summary": summary,
        "findings": all_findings,
        "proactive_suggestions": proactive_suggestions,
        "coverage_gaps": coverage_gaps
    }
    
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
