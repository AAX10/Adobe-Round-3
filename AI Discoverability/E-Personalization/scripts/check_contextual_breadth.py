import sys
import json
import urllib.request
import urllib.error
from html.parser import HTMLParser

class CoreTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.in_h1 = False
        self.in_p = False
        self.p_count = 0
        
        self.title = ""
        self.meta_desc = ""
        self.h1 = ""
        self.first_p = ""
        
    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            attrs_dict = dict(attrs)
            if attrs_dict.get("name", "").lower() == "description":
                self.meta_desc = attrs_dict.get("content", "")
        elif tag == "h1":
            self.in_h1 = True
        elif tag == "p":
            if self.p_count == 0:
                self.in_p = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "h1":
            self.in_h1 = False
        elif tag == "p":
            if self.in_p:
                self.in_p = False
                self.p_count += 1

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif self.in_h1:
            self.h1 += data
        elif self.in_p:
            self.first_p += data

def analyze_breadth(text):
    text = text.lower()
    # Simplified deterministic checks for demonstration
    local_markers = ["austin", "dallas", "houston", "neighborhood", "local", "city", "county"]
    global_markers = ["texas", "usa", "national", "statewide", "country", "global", "everywhere", "online"]
    
    local_count = sum(1 for m in local_markers if m in text)
    global_count = sum(1 for m in global_markers if m in text)
    
    return local_count, global_count

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"findings": []}))
        sys.exit(0)
        
    url = sys.argv[1]
    
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'ContextualBreadthAudit/1.0'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        # Fails gracefully
        print(json.dumps({"findings": []}))
        sys.exit(0)
        
    parser = CoreTextParser()
    parser.feed(html)
    
    core_text = f"{parser.title} {parser.meta_desc} {parser.h1} {parser.first_p}"
    
    local_count, global_count = analyze_breadth(core_text)
    
    findings = []
    
    if local_count > 0 and global_count == 0:
        findings.append({
            "id": "F-001",
            "title": "Hyper-Localized Entity Definition",
            "severity": "high",
            "evidence": f"Found {local_count} local marker(s) but 0 global/regional fallback markers in primary page identity elements (Title, H1, Meta Desc, First P). Text analyzed: {core_text[:100]}...",
            "suggested_action": {
                "summary": "Add a concise persona-neutral and region-agnostic entity definition that identifies the broader service footprint independent of a single city-specific framing.",
                "priority": "high"
            }
        })
        
    print(json.dumps({"findings": findings}, indent=2))

if __name__ == "__main__":
    main()
