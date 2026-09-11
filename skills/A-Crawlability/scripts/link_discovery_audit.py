#!/usr/bin/env python3
"""
link_discovery_audit.py — Compare static vs rendered link graphs for crawl discovery gaps.

Supports hypothesis A-002: Non-Crawlable Navigation / JS-Only Discovery.

Usage:
    python link_discovery_audit.py --url https://example.com [--output results.json]
    python link_discovery_audit.py --help

Dependencies: requests, beautifulsoup4, lxml
Optional: playwright (for rendered link comparison)
"""

import argparse
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin, urldefrag

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package required. Install: pip install requests", file=sys.stderr)
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: 'beautifulsoup4' package required. Install: pip install beautifulsoup4 lxml", file=sys.stderr)
    sys.exit(1)

DEFAULT_TIMEOUT = 15
MAX_SITEMAP_URLS = 500
MAX_LINKS = 1000


def normalize_url(url: str, base_url: str) -> str:
    """Normalize a URL: resolve relative, remove fragment, strip trailing slash."""
    if not url or url.startswith(("javascript:", "mailto:", "tel:", "data:", "#")):
        return None
    try:
        full = urljoin(base_url, url)
        defragged, _ = urldefrag(full)
        # Strip trailing slash for consistency (except root)
        parsed = urlparse(defragged)
        if parsed.path != "/" and defragged.endswith("/"):
            defragged = defragged.rstrip("/")
        return defragged
    except Exception:
        return None


def is_same_domain(url: str, base_url: str) -> bool:
    """Check if a URL belongs to the same domain or subdomain."""
    try:
        url_host = urlparse(url).netloc.lower()
        base_host = urlparse(base_url).netloc.lower()
        return url_host == base_host or url_host.endswith("." + base_host)
    except Exception:
        return False


def extract_static_links(html: str, base_url: str) -> list:
    """Extract all <a href> links from static HTML."""
    soup = BeautifulSoup(html, "lxml")
    links = []
    seen = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "")
        normalized = normalize_url(href, base_url)
        if normalized and normalized not in seen and is_same_domain(normalized, base_url):
            links.append({
                "url": normalized,
                "text": a_tag.get_text(strip=True)[:100],
                "raw_href": href,
            })
            seen.add(normalized)

        if len(links) >= MAX_LINKS:
            break

    return links


def detect_js_navigation_patterns(html: str) -> list:
    """Detect JavaScript-only navigation patterns in HTML."""
    patterns = []
    soup = BeautifulSoup(html, "lxml")

    # onclick handlers on non-link elements
    for elem in soup.find_all(attrs={"onclick": True}):
        if elem.name != "a":
            onclick = elem.get("onclick", "")
            if any(kw in onclick.lower() for kw in ["location", "navigate", "href", "window.open"]):
                patterns.append({
                    "type": "onclick_navigation",
                    "element": elem.name,
                    "text": elem.get_text(strip=True)[:100],
                    "onclick": onclick[:200],
                })

    # Buttons that might trigger navigation
    for btn in soup.find_all("button"):
        text = btn.get_text(strip=True).lower()
        if any(kw in text for kw in ["load more", "show more", "view all", "see more", "next page", "next"]):
            has_link = btn.find("a", href=True)
            if not has_link:
                patterns.append({
                    "type": "js_only_pagination",
                    "element": "button",
                    "text": btn.get_text(strip=True)[:100],
                })

    # Divs/spans with role="link" but no href
    for elem in soup.find_all(attrs={"role": "link"}):
        if elem.name != "a" and not elem.get("href"):
            patterns.append({
                "type": "role_link_no_href",
                "element": elem.name,
                "text": elem.get_text(strip=True)[:100],
            })

    return patterns[:50]  # Bound output


def fetch_sitemap_urls(base_url: str, timeout: int = DEFAULT_TIMEOUT) -> list:
    """Fetch and parse sitemap.xml for declared URLs."""
    parsed = urlparse(base_url)
    sitemap_urls_to_try = [
        f"{parsed.scheme}://{parsed.netloc}/sitemap.xml",
        f"{parsed.scheme}://{parsed.netloc}/sitemap_index.xml",
    ]

    all_urls = set()

    for sitemap_url in sitemap_urls_to_try:
        try:
            resp = requests.get(
                sitemap_url,
                timeout=timeout,
                headers={"User-Agent": "Mozilla/5.0 (compatible; AuditBot/1.0)"},
            )
            if resp.status_code != 200:
                continue

            root = ET.fromstring(resp.content)
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

            # Check for sitemap index
            for sitemap in root.findall(".//sm:sitemap/sm:loc", ns):
                if sitemap.text:
                    all_urls.add(sitemap.text.strip())

            # Check for URL entries
            for url_elem in root.findall(".//sm:url/sm:loc", ns):
                if url_elem.text:
                    all_urls.add(url_elem.text.strip())

            if len(all_urls) >= MAX_SITEMAP_URLS:
                break

        except ET.ParseError:
            continue
        except Exception:
            continue

    return list(all_urls)[:MAX_SITEMAP_URLS]


def run_audit(target_url: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Run the full link discovery audit."""
    audit_start = datetime.now(timezone.utc).isoformat()

    # Step 1: Fetch page HTML
    try:
        resp = requests.get(
            target_url,
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; AuditBot/1.0)",
                "Accept": "text/html",
            },
            allow_redirects=True,
        )
        html = resp.text
        final_url = str(resp.url)
        fetch_status = resp.status_code
    except Exception as e:
        return {
            "check_id": "A-002",
            "site": target_url,
            "timestamp": audit_start,
            "status": "error",
            "severity": None,
            "reason": f"Failed to fetch page: {str(e)[:200]}",
            "evidence": {},
        }

    # Step 2: Extract static links
    static_links = extract_static_links(html, final_url)
    static_urls = set(link["url"] for link in static_links)

    # Step 3: Detect JS navigation patterns
    js_patterns = detect_js_navigation_patterns(html)

    # Step 4: Fetch sitemap URLs
    sitemap_urls = fetch_sitemap_urls(target_url, timeout)
    sitemap_url_set = set(sitemap_urls)

    # Step 5: Analyze coverage
    # URLs in sitemap but NOT in static links (potential JS-only or orphaned)
    sitemap_only = sitemap_url_set - static_urls
    # URLs in both
    in_both = sitemap_url_set & static_urls

    # Step 6: Determine findings
    has_js_patterns = len(js_patterns) > 0
    has_sitemap = len(sitemap_urls) > 0
    static_link_count = len(static_links)

    # Build finding assessment
    findings = []

    if has_js_patterns:
        for pattern in js_patterns:
            findings.append({
                "type": "js_navigation_pattern",
                "detail": pattern,
                "note": "JavaScript-only navigation detected; destinations may not be crawlable",
            })

    if len(sitemap_only) > 0 and static_link_count > 0:
        coverage_ratio = len(in_both) / len(sitemap_url_set) if sitemap_url_set else 1.0
        if coverage_ratio < 0.5:
            findings.append({
                "type": "low_link_sitemap_overlap",
                "detail": {
                    "sitemap_urls": len(sitemap_urls),
                    "static_links_on_page": static_link_count,
                    "overlap": len(in_both),
                    "sitemap_only": len(sitemap_only),
                    "coverage_ratio": round(coverage_ratio, 3),
                },
                "note": (
                    f"Only {round(coverage_ratio * 100, 1)}% of sitemap URLs appear as "
                    f"static links on this page. Many URLs may rely on alternate discovery paths."
                ),
            })

    # Severity
    if len(findings) == 0:
        status = "pass"
        severity = None
    elif any(f["type"] == "js_navigation_pattern" and
             f["detail"].get("type") == "js_only_pagination" for f in findings):
        status = "finding"
        severity = "medium"
    elif has_js_patterns:
        status = "finding"
        severity = "low"
    else:
        status = "finding"
        severity = "info"

    return {
        "check_id": "A-002",
        "site": target_url,
        "timestamp": audit_start,
        "status": status,
        "severity": severity,
        "evidence": {
            "page_fetched": final_url,
            "fetch_status": fetch_status,
            "static_links_found": static_link_count,
            "internal_static_links": len([l for l in static_links if is_same_domain(l["url"], final_url)]),
            "sitemap_available": has_sitemap,
            "sitemap_urls_found": len(sitemap_urls),
            "js_navigation_patterns_detected": len(js_patterns),
            "js_patterns": js_patterns[:10],
            "sitemap_link_overlap": len(in_both) if has_sitemap else None,
            "sitemap_only_urls_sample": list(sitemap_only)[:10] if sitemap_only else [],
        },
        "reason": (
            f"Found {len(js_patterns)} JavaScript-only navigation patterns. "
            f"Static links: {static_link_count}. Sitemap URLs: {len(sitemap_urls)}."
            if has_js_patterns
            else f"No JavaScript-only navigation patterns detected. "
                 f"Static links: {static_link_count}. Sitemap URLs: {len(sitemap_urls)}."
        ),
        "suggested_action": {
            "summary": (
                "Ensure all important destination pages are represented by standard "
                "<a href> links in the HTML. For paginated content, use crawlable links "
                "instead of JavaScript-only 'Load More' handlers. Include all important "
                "URLs in the sitemap."
            ),
            "priority": severity,
        } if status == "finding" else None,
        "findings": findings,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Audit link discovery for non-crawlable navigation (A-002).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python link_discovery_audit.py --url https://example.com
  python link_discovery_audit.py --url https://example.com --output results.json
        """,
    )
    parser.add_argument("--url", required=True, help="URL of the page to audit")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"Request timeout (default: {DEFAULT_TIMEOUT}s)")

    args = parser.parse_args()

    result = run_audit(args.url, args.timeout)

    output_json = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output_json)

    sys.exit(0 if result["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
