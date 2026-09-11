"""
utils_html.py — HTML parsing utilities for Source Selection Auditor.
Provides content extraction, token counting, SPA detection, and heading analysis.
"""

import re
from bs4 import BeautifulSoup, Tag, NavigableString

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def fetch_html(url: str) -> str:
    """Fetch HTML using requests (no browser automation)."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return ""



def count_tokens(text: str) -> int:
    """Simple whitespace tokenizer. Strips punctuation-only tokens."""
    if not text:
        return 0
    words = text.split()
    return sum(1 for w in words if re.search(r"\w", w))


def detect_spa_placeholder(soup: BeautifulSoup) -> bool:
    """Returns True if the page is an un-rendered SPA shell."""
    spa_ids = {"root", "app", "__next", "__nuxt"}
    for sid in spa_ids:
        el = soup.find(id=sid)
        if el and count_tokens(el.get_text(separator=" ", strip=True)) < 30:
            # Confirm overall page text is also sparse
            total = count_tokens(soup.get_text(separator=" ", strip=True))
            if total < 100:
                return True
    return False


def _text_density(tag: Tag) -> float:
    """Return ratio of direct text length to total HTML length for a tag."""
    html_len = len(str(tag))
    if html_len == 0:
        return 0.0
    text_len = len(tag.get_text(separator=" ", strip=True))
    return text_len / html_len


def detect_main_content(soup: BeautifulSoup) -> Tag:
    """Locate the primary content container.
    Priority: <main> > <article> > role='main' > largest text-dense block."""
    # 1) Semantic tags
    main = soup.find("main")
    if main and count_tokens(main.get_text(separator=" ", strip=True)) > 20:
        return main

    article = soup.find("article")
    if article and count_tokens(article.get_text(separator=" ", strip=True)) > 20:
        return article

    role_main = soup.find(attrs={"role": "main"})
    if role_main and count_tokens(role_main.get_text(separator=" ", strip=True)) > 20:
        return role_main

    # 2) Heuristic: find the div/section with highest text density
    best = None
    best_density = 0.0
    for tag in soup.find_all(["div", "section"]):
        tokens = count_tokens(tag.get_text(separator=" ", strip=True))
        if tokens < 30:
            continue
        density = _text_density(tag)
        if density > best_density:
            best_density = density
            best = tag

    return best if best else soup.body if soup.body else soup


def get_container_tokens(soup: BeautifulSoup) -> int:
    """Count all tokens in the document body."""
    body = soup.body if soup.body else soup
    return count_tokens(body.get_text(separator=" ", strip=True))


def extract_headings_with_content(soup: BeautifulSoup) -> list:
    """For each heading (h1-h6), find the next content block and measure distance."""
    results = []
    main = detect_main_content(soup)
    if not main:
        return results

    for level in range(1, 7):
        for heading in main.find_all(f"h{level}"):
            heading_text = heading.get_text(strip=True)
            if not heading_text:
                continue

            # Walk siblings to find next paragraph-like element
            next_content = None
            char_distance = 0
            intervening_elements = []
            accumulated_chars = 0

            sibling = heading.next_sibling
            while sibling:
                if isinstance(sibling, NavigableString):
                    text = sibling.strip()
                    if text:
                        accumulated_chars += len(text)
                elif isinstance(sibling, Tag):
                    if sibling.name in ("p", "ul", "ol", "div", "blockquote", "table"):
                        sib_text = sibling.get_text(strip=True)
                        if len(sib_text) > 20:
                            next_content = sib_text
                            char_distance = accumulated_chars
                            break
                    # Count intervening non-content elements
                    tag_text = sibling.get_text(strip=True)
                    accumulated_chars += len(tag_text)
                    if tag_text:
                        intervening_elements.append(sibling.name)
                sibling = sibling.next_sibling

            results.append({
                "heading_tag": f"h{level}",
                "heading_text": heading_text,
                "heading_level": level,
                "next_content_text": (next_content or "")[:200],
                "char_distance": char_distance,
                "intervening_elements": intervening_elements,
            })

    return results
