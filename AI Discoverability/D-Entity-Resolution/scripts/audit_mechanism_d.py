import json
import re
import sys
import io
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import jellyfish

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def fetch_html(url: str) -> str:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        return resp.text
    except:
        return ""

def parse_json_ld(html_content: str) -> list:
    soup = BeautifulSoup(html_content, "html.parser")
    nodes = []
    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string: continue
        try:
            data = json.loads(script.string)
            if isinstance(data, list): nodes.extend(data)
            elif isinstance(data, dict):
                if "@graph" in data: nodes.extend(data["@graph"])
                else: nodes.append(data)
        except: continue
    return nodes

def evaluate_h1_graph_connectivity(nodes: list) -> dict:
    org_nodes = [n for n in nodes if n.get("@type") == "Organization"]
    org_ids = {n.get("@id") for n in org_nodes if "@id" in n}
    
    evidence = []
    if not org_nodes:
        evidence.append("No Organization node found in JSON-LD.")
    elif not org_ids:
        evidence.append("Organization node lacks a canonical @id.")
    
    # Check sub-entities
    unlinked = 0
    total_refs = 0
    for node in nodes:
        for prop in ["brand", "publisher", "author", "itemReviewed"]:
            if prop in node:
                total_refs += 1
                val = node[prop]
                if isinstance(val, str) or (isinstance(val, dict) and "@id" not in val):
                    unlinked += 1
                    evidence.append(f"Node '{node.get('@type', 'Unknown')}' uses unlinked string/object for '{prop}'.")

    severity = "critical" if not org_ids else ("high" if unlinked > 0 else "none")
    
    return {
        "id": "D-001",
        "title": "Entity Graph Connectivity Deficit",
        "severity": severity,
        "evidence": " ".join(evidence[:3]) if evidence else "Graph is connected properly with @id pointers.",
        "suggested_action": {
            "summary": "Ensure the canonical Organization has an absolute @id, and all child entities (Article, Product) reference it explicitly.",
            "priority": severity
        }
    }

def evaluate_h2_external_identity(nodes: list) -> dict:
    org_nodes = [n for n in nodes if n.get("@type") == "Organization"]
    if not org_nodes:
        return None # H1 already caught this
    
    same_as = org_nodes[0].get("sameAs", [])
    if isinstance(same_as, str): same_as = [same_as]
    
    evidence = []
    kg_anchors = [u for u in same_as if any(d in u.lower() for d in ['wikidata', 'wikipedia'])]
    
    if not same_as:
        evidence.append("Organization lacks sameAs identity anchors.")
        severity = "high"
    elif not kg_anchors:
        evidence.append(f"Found {len(same_as)} sameAs links, but no authoritative Knowledge Graph anchors (Wikidata/Wikipedia).")
        severity = "medium"
    else:
        severity = "none"
        
    return {
        "id": "D-002",
        "title": "External Identity Grounding Deficit",
        "severity": severity,
        "evidence": " ".join(evidence) if evidence else "Authoritative Knowledge Graph anchors found.",
        "suggested_action": {
            "summary": "Add sameAs pointers resolving to Wikidata, Wikipedia, or authoritative financial registries.",
            "priority": severity
        }
    }

def run_audit(url: str):
    html = fetch_html(url)
    nodes = parse_json_ld(html)
    
    findings = []
    
    h1 = evaluate_h1_graph_connectivity(nodes)
    if h1["severity"] != "none": findings.append(h1)
        
    h2 = evaluate_h2_external_identity(nodes)
    if h2 and h2["severity"] != "none": findings.append(h2)
    
    # Mocking H3 and H4 for brevity, in production these parse DOM and regex claims
    # findings.append(h3)
    # findings.append(h4)
    
    report = {
        "site": url,
        "summary": {
            "total_findings": len(findings),
            "critical": sum(1 for f in findings if f["severity"] == "critical"),
            "high": sum(1 for f in findings if f["severity"] == "high"),
            "medium": sum(1 for f in findings if f["severity"] == "medium")
        },
        "findings": findings
    }
    
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "https://www.example.com"
    run_audit(target)
