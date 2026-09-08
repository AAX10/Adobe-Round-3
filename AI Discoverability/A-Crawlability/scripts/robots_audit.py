#!/usr/bin/env python3
"""
robots_audit.py — Fetch and parse robots.txt, test candidate URLs against rules.

Supports hypothesis A-001: Crawl-Blocked Important Content.

Usage:
    python robots_audit.py --url https://example.com [--urls-file urls.txt] [--output results.json]
    python robots_audit.py --help

Dependencies: requests, urllib.robotparser (stdlib)
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package required. Install: pip install requests", file=sys.stderr)
    sys.exit(1)

# Common administrative/private path patterns that should NOT be flagged
ADMIN_PATH_PATTERNS = [
    r'^/admin',
    r'^/wp-admin',
    r'^/wp-login',
    r'^/api/internal',
    r'^/staging',
    r'^/internal',
    r'^/cgi-bin',
    r'^/tmp',
    r'^/\.well-known',
    r'^/debug',
    r'^/test/',
    r'^/dev/',
    r'^/phpmyadmin',
    r'^/server-status',
]

# User agents to test
CRAWL_USER_AGENTS = ['*', 'Googlebot', 'GPTBot', 'ChatGPT-User', 'Bingbot', 'anthropic-ai']

DEFAULT_TIMEOUT = 15
MAX_URLS_TO_TEST = 200


def fetch_robots_txt(base_url: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Fetch and return robots.txt content and metadata."""
    parsed = urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    result = {
        "robots_url": robots_url,
        "status": None,
        "content": None,
        "fetch_error": None,
        "size_bytes": 0,
        "sitemaps": [],
    }

    try:
        resp = requests.get(
            robots_url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; AuditBot/1.0)"},
            allow_redirects=True,
        )
        result["status"] = resp.status_code
        if resp.status_code == 200:
            result["content"] = resp.text
            result["size_bytes"] = len(resp.text)
            # Extract sitemaps
            for line in resp.text.splitlines():
                stripped = line.strip()
                if stripped.lower().startswith("sitemap:"):
                    sitemap_url = stripped.split(":", 1)[1].strip()
                    if sitemap_url:
                        result["sitemaps"].append(sitemap_url)
        elif resp.status_code == 404:
            result["content"] = None  # No robots.txt = allow all
        else:
            result["fetch_error"] = f"Unexpected status: {resp.status_code}"
    except requests.exceptions.Timeout:
        result["fetch_error"] = "Timeout fetching robots.txt"
    except requests.exceptions.ConnectionError as e:
        result["fetch_error"] = f"Connection error: {str(e)[:200]}"
    except Exception as e:
        result["fetch_error"] = f"Error: {str(e)[:200]}"

    return result


def parse_robots_rules(robots_content: str, base_url: str) -> dict:
    """Parse robots.txt and extract rules per user-agent."""
    if not robots_content:
        return {"rules": {}, "raw_directives": []}

    rules = {}
    raw_directives = []
    current_agents = []

    for line in robots_content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if ":" not in stripped:
            continue

        directive, value = stripped.split(":", 1)
        directive = directive.strip().lower()
        value = value.strip()

        raw_directives.append({"directive": directive, "value": value})

        if directive == "user-agent":
            current_agents = [value]
        elif directive in ("disallow", "allow"):
            for agent in current_agents:
                if agent not in rules:
                    rules[agent] = []
                rules[agent].append({
                    "type": directive,
                    "path": value,
                })

    return {"rules": rules, "raw_directives": raw_directives}


def is_admin_path(path: str) -> bool:
    """Check if a URL path matches known administrative/private patterns."""
    for pattern in ADMIN_PATH_PATTERNS:
        if re.match(pattern, path, re.IGNORECASE):
            return True
    return False


def test_url_against_robots(url: str, robots_content: str, base_url: str) -> dict:
    """Test a URL against robots.txt rules for each user agent."""
    parsed = urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    results = {}
    for agent in CRAWL_USER_AGENTS:
        rp = RobotFileParser()
        rp.set_url(robots_url)
        if robots_content:
            rp.parse(robots_content.splitlines())
            can_fetch = rp.can_fetch(agent, url)
        else:
            can_fetch = True  # No robots.txt = allow all

        results[agent] = {
            "allowed": can_fetch,
        }

    return results


def check_url_accessible(url: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Make a HEAD request to check if URL returns usable content."""
    try:
        resp = requests.head(
            url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; AuditBot/1.0)"},
            allow_redirects=True,
        )
        return {
            "status_code": resp.status_code,
            "accessible": 200 <= resp.status_code < 400,
            "final_url": str(resp.url),
            "error": None,
        }
    except Exception as e:
        return {
            "status_code": None,
            "accessible": False,
            "final_url": None,
            "error": str(e)[:200],
        }


def run_audit(base_url: str, candidate_urls: list, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Run the full robots.txt audit."""
    audit_start = datetime.now(timezone.utc).isoformat()

    # Step 1: Fetch robots.txt
    robots_data = fetch_robots_txt(base_url, timeout)

    # Step 2: Parse rules
    parsed_rules = parse_robots_rules(robots_data.get("content", ""), base_url)

    # Step 3: Test each URL
    url_results = []
    blocked_important = []

    for url in candidate_urls[:MAX_URLS_TO_TEST]:
        parsed_url = urlparse(url)
        url_path = parsed_url.path or "/"

        # Test against robots
        robot_results = test_url_against_robots(url, robots_data.get("content", ""), base_url)

        # Determine if blocked by any relevant agent
        blocked_agents = [
            agent for agent, result in robot_results.items()
            if not result["allowed"]
        ]

        is_blocked = len(blocked_agents) > 0
        is_admin = is_admin_path(url_path)

        result = {
            "url": url,
            "path": url_path,
            "is_blocked": is_blocked,
            "blocked_by_agents": blocked_agents,
            "is_admin_path": is_admin,
            "robot_results": robot_results,
        }

        # Only flag as important-blocked if blocked AND not an admin path
        if is_blocked and not is_admin:
            # Check if actually accessible (serves content)
            access = check_url_accessible(url, timeout)
            result["accessibility_check"] = access

            if access["accessible"]:
                result["finding"] = True
                result["finding_reason"] = (
                    f"URL serves public content (status {access['status_code']}) "
                    f"but is blocked by robots.txt for agents: {', '.join(blocked_agents)}"
                )
                blocked_important.append(result)
            else:
                result["finding"] = False
                result["finding_reason"] = "URL is blocked but does not serve accessible content"
        else:
            result["finding"] = False
            if is_admin:
                result["finding_reason"] = "Blocked path is administrative/private — expected"
            elif not is_blocked:
                result["finding_reason"] = "URL is not blocked by robots.txt"

        url_results.append(result)
        time.sleep(0.2)  # Respectful delay

    # Step 4: Determine severity
    total_tested = len(url_results)
    total_blocked_important = len(blocked_important)

    if total_blocked_important == 0:
        severity = "pass"
        status = "pass"
    elif total_tested > 0 and total_blocked_important / total_tested > 0.5:
        severity = "critical"
        status = "finding"
    elif total_tested > 0 and total_blocked_important / total_tested > 0.25:
        severity = "high"
        status = "finding"
    elif total_blocked_important >= 3:
        severity = "medium"
        status = "finding"
    else:
        severity = "low"
        status = "finding"

    return {
        "check_id": "A-001",
        "site": base_url,
        "timestamp": audit_start,
        "status": status,
        "severity": severity,
        "evidence": {
            "robots_txt": {
                "url": robots_data["robots_url"],
                "status": robots_data["status"],
                "size_bytes": robots_data["size_bytes"],
                "sitemaps_declared": robots_data["sitemaps"],
                "fetch_error": robots_data["fetch_error"],
            },
            "rules_summary": {
                "user_agents_with_rules": list(parsed_rules["rules"].keys()),
                "total_directives": len(parsed_rules["raw_directives"]),
            },
            "urls_tested": total_tested,
            "urls_blocked_important": total_blocked_important,
            "blocked_important_urls": [
                {
                    "url": r["url"],
                    "blocked_by": r["blocked_by_agents"],
                    "status_code": r.get("accessibility_check", {}).get("status_code"),
                }
                for r in blocked_important
            ],
        },
        "reason": (
            f"Tested {total_tested} candidate URLs; "
            f"{total_blocked_important} important public URLs are blocked by robots.txt."
            if total_blocked_important > 0
            else f"Tested {total_tested} candidate URLs; none are inappropriately blocked by robots.txt."
        ),
        "suggested_action": {
            "summary": (
                "Remove or narrow robots.txt Disallow rules that block important public content. "
                "Use more specific paths to exclude only administrative or private areas."
            ),
            "priority": severity,
        } if status == "finding" else None,
        "url_results": url_results,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Audit robots.txt for blocked important content (A-001).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python robots_audit.py --url https://example.com
  python robots_audit.py --url https://example.com --urls-file important_urls.txt
  python robots_audit.py --url https://example.com --output results.json
        """,
    )
    parser.add_argument("--url", required=True, help="Base URL of the site to audit")
    parser.add_argument("--urls-file", help="File with candidate URLs to test (one per line)")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})")

    args = parser.parse_args()

    # Collect candidate URLs
    candidate_urls = []
    if args.urls_file:
        try:
            with open(args.urls_file, "r") as f:
                candidate_urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        except FileNotFoundError:
            print(f"ERROR: URLs file not found: {args.urls_file}", file=sys.stderr)
            sys.exit(1)

    if not candidate_urls:
        # Generate basic candidate URLs from common paths
        parsed = urlparse(args.url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        candidate_urls = [
            base + "/",
            base + "/about",
            base + "/products",
            base + "/pricing",
            base + "/contact",
            base + "/blog",
            base + "/faq",
            base + "/support",
            base + "/docs",
            base + "/careers",
        ]
        print(f"No URLs file provided; testing {len(candidate_urls)} common paths.", file=sys.stderr)

    # Run audit
    result = run_audit(args.url, candidate_urls, args.timeout)

    # Output
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
