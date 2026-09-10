import sys
import json
import urllib.request
import urllib.error
from html.parser import HTMLParser

class JSONLDParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.is_jsonld = False
        self.jsonld_contents = []
        self.current_content = ""

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            attrs_dict = dict(attrs)
            if attrs_dict.get("type", "").lower() == "application/ld+json":
                self.in_script = True
                self.is_jsonld = True
                self.current_content = ""

    def handle_endtag(self, tag):
        if tag == "script" and self.in_script and self.is_jsonld:
            self.in_script = False
            self.is_jsonld = False
            try:
                data = json.loads(self.current_content)
                self.jsonld_contents.append(data)
            except json.JSONDecodeError:
                pass

    def handle_data(self, data):
        if self.in_script and self.is_jsonld:
            self.current_content += data

def check_schema(schema_data):
    findings = []
    
    # Handle both single objects and arrays of objects
    items = schema_data if isinstance(schema_data, list) else [schema_data]
    
    for item in items:
        # Some JSON-LD structures are nested in @graph
        if "@graph" in item:
            items.extend(item["@graph"])
            continue
            
        schema_type = item.get("@type", "")
        if isinstance(schema_type, list):
            schema_type = schema_type[0]
            
        if schema_type in ["Organization", "LocalBusiness"]:
            has_address = "address" in item
            has_area_served = "areaServed" in item
            
            if has_address and not has_area_served:
                findings.append({
                    "id": "F-002",
                    "title": "Strict Schema Localization Risk",
                    "severity": "high",
                    "evidence": f"Found '{schema_type}' schema with an 'address' property but missing 'areaServed'. This restricts the entity to a physical bounding box.",
                    "suggested_action": {
                        "summary": "Add the 'areaServed' property to the structured data if the organization serves a broader region or operates online.",
                        "priority": "high"
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
        headers={'User-Agent': 'SchemaLocalizationAudit/1.0'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(json.dumps({"findings": []}))
        sys.exit(0)
        
    parser = JSONLDParser()
    parser.feed(html)
    
    all_findings = []
    for schema in parser.jsonld_contents:
        all_findings.extend(check_schema(schema))
        
    print(json.dumps({"findings": all_findings}, indent=2))

if __name__ == "__main__":
    main()
