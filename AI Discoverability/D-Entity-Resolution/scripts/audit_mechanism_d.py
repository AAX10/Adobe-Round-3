import json
import re
import sys
import io
import datetime
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import jellyfish
from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def is_org(node: dict) -> bool:
    """Helper to catch arrays and subtypes of Organization."""
    t = node.get("@type")
    valid_types = {"Organization", "Corporation", "LocalBusiness"}
    if isinstance(t, list):
        return bool(set(t) & valid_types)
    return t in valid_types

def fetch_html(url: str) -> str:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=HEADERS["User-Agent"])
            # FIX 1: domcontentloaded prevents infinite hangs on tracking pixels
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        return ""

def parse_json_ld(html_content: str) -> list:
    soup = BeautifulSoup(html_content, "html.parser")
    nodes = []
    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string: 
            continue
        try:
            data = json.loads(script.string)
            if isinstance(data, list): 
                nodes.extend(data)
            elif isinstance(data, dict):
                if "@graph" in data and isinstance(data["@graph"], list): 
                    nodes.extend(data["@graph"])
                else: 
                    nodes.append(data)
        except json.JSONDecodeError: 
            continue
    return nodes

def evaluate_hd1_graph_connectivity(nodes: list) -> dict:
    # FIX 2: Set-based type checking
    org_nodes = [n for n in nodes if is_org(n)]
    org_ids = {n.get("@id") for n in org_nodes if "@id" in n}
    
    evidence = []
    severity = "none"
    
    if not org_nodes:
        evidence.append("No Organization/Corporation node found in JSON-LD.")
        severity = "high"
    elif not org_ids:
        evidence.append("Organization node exists but lacks a canonical @id pointer.")
        severity = "high"
        
    seen_ids = {}
    node_collision = False
    for n in nodes:
        nid = n.get("@id")
        ntype = n.get("@type")
        if nid and ntype:
            # Handle list types in collision check
            ntype_str = str(ntype)
            if nid in seen_ids and seen_ids[nid] != ntype_str:
                node_collision = True
                evidence.append(f"Node collision detected: @id '{nid}' assigned to both '{seen_ids[nid]}' and '{ntype_str}'.")
            seen_ids[nid] = ntype_str
            
    if node_collision:
        severity = "critical" 
        
    unlinked_count = 0
    for node in nodes:
        ntype = node.get("@type", "Unknown")
        for prop in ["brand", "publisher", "author", "itemReviewed", "provider"]:
            if prop in node:
                val = node[prop]
                if isinstance(val, str):
                    unlinked_count += 1
                    evidence.append(f"'{ntype}.{prop}' uses plain text string '{val}' instead of @id pointer.")
                elif isinstance(val, dict):
                    ref_id = val.get("@id")
                    if not ref_id:
                        unlinked_count += 1
                        evidence.append(f"'{ntype}.{prop}' is an inline object lacking an @id pointer.")
                    elif org_ids and ref_id not in org_ids:
                        unlinked_count += 1
                        evidence.append(f"'{ntype}.{prop}' @id '{ref_id}' does not match Organization @id.")

    if severity == "none" and unlinked_count > 0:
        severity = "high"

    return {
        "id": "H-D1",
        "title": "Entity Graph Connectivity Deficit",
        "severity": severity,
        "evidence": " ".join(evidence) if evidence else "Entity graph is fully connected with valid @id pointers.",
        "suggested_action": {
            "summary": "Ensure the primary Organization defines an absolute @id and all sub-entities reference it explicitly.",
            "priority": severity
        }
    }

def evaluate_hd2_external_identity(nodes: list) -> dict:
    org_nodes = [n for n in nodes if is_org(n)]
    if not org_nodes:
        return None

    same_as = org_nodes[0].get("sameAs", [])
    if isinstance(same_as, str): 
        same_as = [same_as]

    evidence = []
    severity = "none"
    
    kg_anchors = [u for u in same_as if any(d in u.lower() for d in ['wikidata.org', 'wikipedia.org', 'google.com/search'])]
    
    if not same_as:
        evidence.append("Organization schema lacks sameAs identity anchors.")
        severity = "high"
    elif not kg_anchors:
        evidence.append(f"Found {len(same_as)} sameAs links, but zero authoritative Knowledge Graph anchors (Wikidata/Wikipedia).")
        severity = "high"

    broken_links = 0
    domain_drift = 0
    unverifiable_links = 0

    for url in same_as[:5]: 
        try:
            parsed_orig = urlparse(url)
            resp = requests.head(url, allow_redirects=True, headers=HEADERS, timeout=5)
            if resp.status_code >= 400:
                resp = requests.get(url, allow_redirects=True, headers=HEADERS, timeout=5)
            
            if resp.status_code in [401, 403, 429, 999]:
                unverifiable_links += 1
                evidence.append(f"sameAs URL '{url}' returned anti-bot HTTP {resp.status_code} (Unverifiable).")
            elif resp.status_code >= 400:
                broken_links += 1
                evidence.append(f"sameAs URL '{url}' is broken (HTTP {resp.status_code}).")
            else:
                parsed_final = urlparse(resp.url)
                if parsed_orig.netloc.replace("www.", "") != parsed_final.netloc.replace("www.", ""):
                    domain_drift += 1
                    evidence.append(f"sameAs URL '{url}' redirected out-of-domain to '{resp.url}'.")
        except Exception:
            broken_links += 1
            evidence.append(f"sameAs URL '{url}' failed to resolve.")

    if domain_drift > 0:
        severity = "critical" 
    elif broken_links > 0 and severity != "critical":
        severity = "high"

    return {
        "id": "H-D2",
        "title": "External Identity Grounding Deficit",
        "severity": severity,
        "evidence": " ".join(evidence) if evidence else "Valid, high-authority Knowledge Graph identity anchors found.",
        "suggested_action": {
            "summary": "Add resolving sameAs URLs pointing to Wikidata QIDs or Wikipedia articles.",
            "priority": severity
        }
    }

def evaluate_hd3_cross_modal_consistency(html_content: str, nodes: list) -> dict:
    org_nodes = [n for n in nodes if is_org(n)]
    if not org_nodes:
        return None

    schema_name = org_nodes[0].get("name", "")
    soup = BeautifulSoup(html_content, "html.parser")
    page_title = soup.title.string if soup.title else ""
    h1_text = soup.find("h1").get_text() if soup.find("h1") else ""

    def normalize(text):
        if not text: return ""
        text = text.lower()
        text = re.sub(r"\b(inc|llc|corp|ltd|limited|pvt|private)\b", "", text)
        return re.sub(r"[^\w\s]", "", text).strip()

    norm_schema = normalize(schema_name)
    norm_dom = normalize(f"{page_title} {h1_text}")

    if not norm_schema or not norm_dom:
        return None

    # FIX 3: Substring Pre-Check to skip Jaro-Winkler penalties on exact matches inside longer strings
    if norm_schema in norm_dom:
        similarity = 1.0
    else:
        similarity = jellyfish.jaro_winkler_similarity(norm_schema, norm_dom[:200])
    
    evidence = []
    severity = "none"
    
    if similarity < 0.4:
        severity = "high"
        evidence.append(f"Severe schema vs DOM name contradiction detected (Jaro-Winkler: {similarity:.2f}). Schema: '{schema_name}'.")
    elif similarity < 0.75:
        severity = "medium"
        evidence.append(f"Moderate DOM/Schema naming variance detected (Jaro-Winkler: {similarity:.2f}).")

    return {
        "id": "H-D3",
        "title": "Cross-Modal Attribute Contradiction",
        "severity": severity,
        "evidence": " ".join(evidence) if evidence else f"High cross-modal string consistency verified (Jaro-Winkler: {similarity:.2f}).",
        "suggested_action": {
            "summary": "Align JSON-LD Organization name with visible <h1> and <title> headers.",
            "priority": severity
        }
    }

def evaluate_hd4_claim_corroboration(html_content: str, nodes: list) -> dict:
    soup = BeautifulSoup(html_content, "html.parser")
    dom_text = soup.get_text()
    
    claim_pattern = r"(\b\d+(\.\d+)?%\b|\$\d+[\d,]*\b|\b\d+\+\s+(users|customers|employees|clients)\b)"
    claims_found = re.findall(claim_pattern, dom_text, re.IGNORECASE)
    
    citations = []
    for n in nodes:
        if "citation" in n:
            citations.append(n["citation"])

    claim_count = len(claims_found)
    citation_count = len(citations)
    
    evidence = []
    severity = "none"
    
    if claim_count > 0 and citation_count == 0:
        severity = "medium"
        evidence.append(f"Detected {claim_count} quantitative claims in DOM text with zero RDF citation properties in schema.")

    return {
        "id": "H-D4",
        "title": "Uncorroborated Factual Claim Deficit",
        "severity": severity,
        "evidence": " ".join(evidence) if evidence else "Quantitative claims are backed by structured citation references or no raw stats present.",
        "suggested_action": {
            "summary": "Embed structured RDF 'citation' properties or outbound links adjacent to quantitative assertions.",
            "priority": severity
        }
    }

def run_audit(url: str):
    html = fetch_html(url)
    if not html:
        print(json.dumps({"error": f"Failed to retrieve HTML payload from {url}"}))
        return

    nodes = parse_json_ld(html)
    findings = []

    h1 = evaluate_hd1_graph_connectivity(nodes)
    if h1 and h1["severity"] != "none": 
        findings.append(h1)

    h2 = evaluate_hd2_external_identity(nodes)
    if h2 and h2["severity"] != "none": 
        findings.append(h2)

    h3 = evaluate_hd3_cross_modal_consistency(html, nodes)
    if h3 and h3["severity"] != "none": 
        findings.append(h3)

    h4 = evaluate_hd4_claim_corroboration(html, nodes)
    if h4 and h4["severity"] != "none": 
        findings.append(h4)

    report = {
        "audited_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "site": url,
        "summary": {
            "total_findings": len(findings),
            "critical": sum(1 for f in findings if f["severity"] == "critical"),
            "high": sum(1 for f in findings if f["severity"] == "high"),
            "medium": sum(1 for f in findings if f["severity"] == "medium"),
            # FIX 4: Schema compliance key rename
            "low": sum(1 for f in findings if f["severity"] == "low")
        },
        "findings": findings
    }

    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "https://www.adobe.com"
    run_audit(target)
