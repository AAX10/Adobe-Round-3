#!/usr/bin/env python3
"""
url_retrieval_audit.py — Test whether important URLs return usable HTTP responses.

Supports hypothesis A-003: Important URL Retrieval Failure.

Usage:
    python url_retrieval_audit.py --url https://example.com [--urls-file urls.txt] [--output results.json]
    python url_retrieval_audit.py --help

Dependencies: requests
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package required. Install: pip install requests", file=sys.stderr)
    sys.exit(1)

DEFAULT_TIMEOUT = 15
MAX_URLS = 100
RETRY_DELAY = 5  # seconds between retries
MAX_RETRIES = 2
MAX_REDIRECTS = 10


def fetch_url_status(url: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Fetch a URL and record detailed retrieval status."""
    result = {
        "url": url,
        "attempts": [],
        "final_status": None,
        "final_url": None,
        "redirect_chain": [],
        "content_type": None,
        "response_time_ms": None,
        "error": None,
        "persistent_failure": False,
    }

    for attempt in range(MAX_RETRIES):
        attempt_result = {
            "attempt": attempt + 1,
            "status_code": None,
            "error": None,
            "response_time_ms": None,
        }

        try:
            start = time.time()
            resp = requests.get(
                url,
                timeout=timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; AuditBot/1.0)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
                allow_redirects=True,
                stream=True,  # Don't download full body
            )
            elapsed_ms = round((time.time() - start) * 1000)

            attempt_result["status_code"] = resp.status_code
            attempt_result["response_time_ms"] = elapsed_ms

            # Record redirect chain
            if resp.history:
                chain = []
                for r in resp.history:
                    chain.append({
                        "status": r.status_code,
                        "url": str(r.url),
                    })
                result["redirect_chain"] = chain

            result["final_status"] = resp.status_code
            result["final_url"] = str(resp.url)
            result["content_type"] = resp.headers.get("Content-Type", "")[:100]
            result["response_time_ms"] = elapsed_ms

            resp.close()

            # If success, no need to retry
            if 200 <= resp.status_code < 400:
                result["attempts"].append(attempt_result)
                break

        except requests.exceptions.Timeout:
            attempt_result["error"] = "timeout"
            result["error"] = "timeout"
        except requests.exceptions.TooManyRedirects:
            attempt_result["error"] = "too_many_redirects"
            result["error"] = "too_many_redirects"
        except requests.exceptions.ConnectionError as e:
            attempt_result["error"] = f"connection_error: {str(e)[:100]}"
            result["error"] = attempt_result["error"]
        except Exception as e:
            attempt_result["error"] = f"error: {str(e)[:100]}"
            result["error"] = attempt_result["error"]

        result["attempts"].append(attempt_result)

        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)

    # Determine persistence
    failed_attempts = [a for a in result["attempts"] if
                       a.get("status_code") is None or a["status_code"] >= 400]

    result["persistent_failure"] = len(failed_attempts) == len(result["attempts"]) and len(result["attempts"]) >= 2

    return result


def classify_failure(result: dict) -> dict:
    """Classify a URL retrieval failure."""
    status = result.get("final_status")
    error = result.get("error")

    if status and 200 <= status < 300:
        return {"class": "success", "description": "URL returns usable content"}
    elif status and 300 <= status < 400:
        return {"class": "redirect", "description": f"Redirect ({status}) to {result.get('final_url', 'unknown')}"}
    elif status == 404:
        return {"class": "not_found", "description": "Content not found (404)"}
    elif status == 410:
        return {"class": "intentionally_removed", "description": "Content intentionally removed (410 Gone)"}
    elif status == 403:
        return {"class": "forbidden", "description": "Access forbidden (403)"}
    elif status == 429:
        return {"class": "rate_limited", "description": "Rate limited (429) — not a site defect"}
    elif status and 400 <= status < 500:
        return {"class": "client_error", "description": f"Client error ({status})"}
    elif status and 500 <= status < 600:
        return {"class": "server_error", "description": f"Server error ({status})"}
    elif error == "timeout":
        return {"class": "timeout", "description": "Request timed out"}
    elif error == "too_many_redirects":
        return {"class": "redirect_loop", "description": "Redirect chain exceeds limit"}
    elif error and "connection_error" in error:
        return {"class": "connection_failure", "description": "Connection failed"}
    else:
        return {"class": "unknown", "description": f"Unknown failure: {error}"}


def run_audit(base_url: str, candidate_urls: list, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Run the full URL retrieval audit."""
    audit_start = datetime.now(timezone.utc).isoformat()

    url_results = []
    failures = []
    successes = []
    rate_limited = []

    for url in candidate_urls[:MAX_URLS]:
        result = fetch_url_status(url, timeout)
        classification = classify_failure(result)
        result["classification"] = classification

        if classification["class"] == "success" or classification["class"] == "redirect":
            successes.append(result)
        elif classification["class"] == "rate_limited":
            rate_limited.append(result)
        elif classification["class"] == "intentionally_removed":
            pass  # 410 Gone is expected, don't count as failure
        else:
            if result["persistent_failure"]:
                failures.append(result)

        url_results.append(result)
        time.sleep(0.3)  # Respectful delay

    total_tested = len(url_results)
    total_persistent_failures = len(failures)
    total_rate_limited = len(rate_limited)

    # Calculate failure rate (excluding rate-limited)
    testable = total_tested - total_rate_limited
    failure_rate = total_persistent_failures / testable if testable > 0 else 0

    # Severity
    if total_persistent_failures == 0:
        status = "pass"
        severity = None
    elif failure_rate > 0.5:
        status = "finding"
        severity = "critical"
    elif failure_rate > 0.25:
        status = "finding"
        severity = "high"
    elif failure_rate > 0.10:
        status = "finding"
        severity = "medium"
    else:
        status = "finding"
        severity = "low"

    return {
        "check_id": "A-003",
        "site": base_url,
        "timestamp": audit_start,
        "status": status,
        "severity": severity,
        "evidence": {
            "urls_tested": total_tested,
            "successful_retrievals": len(successes),
            "persistent_failures": total_persistent_failures,
            "rate_limited": total_rate_limited,
            "failure_rate": round(failure_rate, 3),
            "failure_breakdown": {},
            "failed_urls": [
                {
                    "url": f["url"],
                    "classification": f["classification"]["class"],
                    "final_status": f.get("final_status"),
                    "error": f.get("error"),
                    "attempts": len(f["attempts"]),
                }
                for f in failures
            ],
        },
        "reason": (
            f"Tested {total_tested} URLs; {total_persistent_failures} "
            f"({round(failure_rate * 100, 1)}%) persistently failed to return usable content."
            if total_persistent_failures > 0
            else f"Tested {total_tested} URLs; all returned usable responses."
        ),
        "suggested_action": {
            "summary": (
                "Investigate and resolve persistent HTTP failures for important public URLs. "
                "Fix broken internal links, resolve redirect chains, and repair server errors."
            ),
            "priority": severity,
        } if status == "finding" else None,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Audit URL retrieval for persistent failures (A-003).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python url_retrieval_audit.py --url https://example.com --urls-file important_urls.txt
  python url_retrieval_audit.py --url https://example.com --output results.json
        """,
    )
    parser.add_argument("--url", required=True, help="Base URL of the site")
    parser.add_argument("--urls-file", help="File with URLs to test (one per line)")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"Request timeout (default: {DEFAULT_TIMEOUT}s)")

    args = parser.parse_args()

    candidate_urls = []
    if args.urls_file:
        try:
            with open(args.urls_file, "r") as f:
                candidate_urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        except FileNotFoundError:
            print(f"ERROR: URLs file not found: {args.urls_file}", file=sys.stderr)
            sys.exit(1)

    if not candidate_urls:
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
        ]
        print(f"No URLs file provided; testing {len(candidate_urls)} common paths.", file=sys.stderr)

    result = run_audit(args.url, candidate_urls, args.timeout)

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
