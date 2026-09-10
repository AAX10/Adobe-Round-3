import subprocess
import json
import os

SITES = [
    "https://www.adobe.com",
    "https://www.microsoft.com",
    "https://www.salesforce.com",
    "https://www.ibm.com",
    "https://www.oracle.com"
]

all_results = []
inventory = []

print("Starting batch audit process...")

for site in SITES:
    print(f"[*] Auditing {site}...")
    try:
        result = subprocess.run(
            ["python", "audit_mechanism_d.py", site],
            capture_output=True,
            text=True,
            check=True
        )
        
        try:
            report = json.loads(result.stdout)
            if "error" in report:
                print(f"    -> Error: {report['error']}")
                inventory.append({"site": site, "status": "error", "reason": report['error']})
            else:
                all_results.append(report)
                inventory.append({"site": site, "status": "success", "total_findings": report.get("summary", {}).get("total_findings", 0)})
        except json.JSONDecodeError:
            print(f"    -> Failed to parse JSON output.")
            inventory.append({"site": site, "status": "error", "reason": "JSON decode failed"})
            
    except subprocess.CalledProcessError as e:
        print(f"    -> Subprocess failed: {e}")
        inventory.append({"site": site, "status": "error", "reason": "Subprocess failed"})

# Compute aggregates
total_critical = sum(r.get("summary", {}).get("critical", 0) for r in all_results if "summary" in r)
total_high = sum(r.get("summary", {}).get("high", 0) for r in all_results if "summary" in r)
total_medium = sum(r.get("summary", {}).get("medium", 0) for r in all_results if "summary" in r)

final_result = {
    "mechanism": "D-Entity-Resolution",
    "total_sites_audited": len(SITES),
    "successful_audits": len(all_results),
    "aggregate_findings": {
        "critical": total_critical,
        "high": total_high,
        "medium": total_medium
    }
}

# Write evidence files
os.makedirs("../evidence", exist_ok=True)

with open("../evidence/all_results.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, indent=2)
    
with open("../evidence/site_inventory.json", "w", encoding="utf-8") as f:
    json.dump(inventory, f, indent=2)
    
with open("../final_result.json", "w", encoding="utf-8") as f:
    json.dump(final_result, f, indent=2)

print("\nBatch processing complete! Wrote data to evidence folder and final_result.json.")
