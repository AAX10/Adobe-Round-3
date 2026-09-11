import sys
import json
import urllib.request
import urllib.error
from html.parser import HTMLParser

class ParagraphParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_p = False
        self.paragraphs = []
        self.current_p = ""

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.in_p = True
            self.current_p = ""

    def handle_endtag(self, tag):
        if tag == "p" and self.in_p:
            self.in_p = False
            text = self.current_p.strip()
            if text:
                self.paragraphs.append(text)

    def handle_data(self, data):
        if self.in_p:
            self.current_p += data + " "

def analyze_variance(paragraphs):
    # Simplified deterministic checks for demonstration
    core_services = ["service", "provider", "business", "company", "solution", "product"]
    local_markers = ["austin", "dallas", "houston", "neighborhood", "city", "local"]
    global_markers = ["texas", "usa", "national", "statewide", "country", "global", "everywhere", "online"]
    
    service_only_chunks = 0
    service_with_local = 0
    service_with_global = 0
    
    for p in paragraphs:
        text = p.lower()
        has_service = any(s in text for s in core_services)
        has_local = any(l in text for l in local_markers)
        has_global = any(g in text for g in global_markers)
        
        if has_service:
            if has_local and not has_global:
                service_with_local += 1
            elif has_global:
                service_with_global += 1
            else:
                service_only_chunks += 1
                
    findings = []
    
    # If service terms are frequently chunked with local terms but rarely with global terms
    if service_with_local > 0 and service_with_global == 0 and service_only_chunks == 0:
        findings.append({
            "id": "F-003",
            "title": "Context-Variance Structural Risk (Chunk Fragmentation)",
            "severity": "medium",
            "evidence": f"Analyzed {len(paragraphs)} paragraphs. Core service terms co-occurred exclusively with local geographic markers ({service_with_local} times) and never independently or with global markers. This risks RAG context-drop.",
            "suggested_action": {
                "summary": "Create distinct paragraphs that define the core service independent of local geographic modifiers to ensure safe retrieval for generic queries.",
                "priority": "medium"
            }
        })
        
    return findings

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"findings": []}))
        sys.exit(0)
        
    url = sys.argv[1]
    
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'ContextVarianceAudit/1.0'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(json.dumps({"findings": []}))
        sys.exit(0)
        
    parser = ParagraphParser()
    parser.feed(html)
    
    findings = analyze_variance(parser.paragraphs)
    
    print(json.dumps({"findings": findings}, indent=2))

if __name__ == "__main__":
    main()
