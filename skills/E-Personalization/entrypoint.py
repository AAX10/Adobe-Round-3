import sys
import json
import datetime
from urllib.parse import urlparse
import subprocess
import os

def run_script(script_name, url):
    script_path = os.path.join(os.path.dirname(__file__), 'scripts', script_name)
    try:
        result = subprocess.run(
            [sys.executable, script_path, url],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e.stderr}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from {script_name}: {e}", file=sys.stderr)
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python entrypoint.py <URL>")
        sys.exit(1)
    
    url = sys.argv[1]
    parsed_url = urlparse(url)
    site = parsed_url.netloc or url
    
    scripts = [
        'check_contextual_breadth.py',
        'check_schema_localization.py',
        'check_context_variance.py'
    ]
    
    all_findings = []
    
    for script in scripts:
        script_output = run_script(script, url)
        if script_output and "findings" in script_output:
            all_findings.extend(script_output["findings"])
            
    summary = {
        "total_findings": len(all_findings),
        "critical": sum(1 for f in all_findings if f.get("severity") == "critical"),
        "high": sum(1 for f in all_findings if f.get("severity") == "high"),
        "medium": sum(1 for f in all_findings if f.get("severity") == "medium")
    }
    
    report = {
        "site": site,
        "audited_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "summary": summary,
        "findings": all_findings
    }
    
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
