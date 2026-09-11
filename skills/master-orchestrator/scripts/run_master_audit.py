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
        sev = f.get("severity", "info")
        if sev in summary:
            summary[sev] += 1
            
    report = {
        "site": target,
        "audited_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": summary,
        "findings": all_findings
    }
    
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
