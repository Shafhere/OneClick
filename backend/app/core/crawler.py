"""Respectful, same-site company website crawler for OneClick.

Uses requests/BeautifulSoup first and optionally Playwright for JavaScript-rendered
pages when Playwright is installed. robots.txt rules are respected.
"""
from __future__ import annotations

import ipaddress
import os
import socket
import time
import xml.etree.ElementTree as ET
from collections import deque
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse, urldefrag
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
MAX_PAGES = max(1, min(int(os.getenv("MAX_PAGES", "20")), 50))
TIMEOUT = max(3, min(int(os.getenv("REQUEST_TIMEOUT", "15")), 45))
MAX_BYTES = 3_000_000
USER_AGENT = "OneClickResearchBot/1.2 (+public company research; respectful crawling)"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.8",
}
PRIORITY_TERMS = (
    "about", "company", "who-we-are", "our-story", "mission", "vision",
    "product", "service", "course", "program", "solution", "industry",
    "pricing", "price", "fee", "plan", "contact", "career", "job",
    "placement", "alumni", "partner", "sustain", "impact", "investor",
    "customer", "client", "faq", "press", "news", "team", "leadership",
)
SKIP_TERMS = (
    "logout", "login", "signin", "signup", "cart", "checkout", "privacy-policy",
    "terms-and-conditions", "cookie-policy", "wp-json", ".pdf", ".jpg", ".png",
    ".jpeg", ".webp", ".svg", ".zip", ".mp4", ".css", ".js", "mailto:", "tel:",
)
REDIRECT_CODES = {301, 302, 303, 307, 308}


def normalize_url(url: str) -> str:
    """Normalize HTTP(S) URLs for crawl deduplication."""
    url, _ = urldefrag((url or "").strip())
    p = urlparse(url)
    if p.scheme.lower() not in {"http", "https"} or not p.hostname:
        return ""
    host = p.hostname.lower().rstrip(".")
    try:
        port = p.port
    except ValueError:
        return ""
    netloc = host
    if port and not ((p.scheme.lower() == "http" and port == 80) or (p.scheme.lower() == "https" and port == 443)):
        netloc = f"{host}:{port}"
    path = p.path or "/"
    if path != "/":
        path = path.rstrip("/")
    query = urlencode([
        (k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
        if not k.lower().startswith("utm_")
        and k.lower() not in {"gclid", "fbclid", "mc_cid", "mc_eid"}
    ])
    return urlunparse((p.scheme.lower(), netloc, path, "", query, ""))


def _resolve_public_host(host: str) -> None:
    """Reject private, loopback, link-local, and otherwise non-public IP targets."""
    host = (host or "").lower().rstrip(".")
    if not host or host == "localhost" or host.endswith((".localhost", ".local")):
        raise ValueError("Local addresses cannot be crawled.")
    try:
        addresses = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError("The website hostname could not be resolved.") from exc
    if not addresses:
        raise ValueError("The website hostname could not be resolved.")
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0].split("%", 1)[0])
        if not ip.is_global:
            raise ValueError("Private or non-public addresses cannot be crawled.")


def validate_public_url(url: str) -> str:
    normalized = normalize_url(url)
    parsed = urlparse(normalized)
    if not normalized:
        raise ValueError("Please provide a valid HTTP or HTTPS URL.")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not allowed.")
    _resolve_public_host(parsed.hostname or "")
    return normalized


def _host_aliases(host: str) -> set[str]:
    """Treat example.com and www.example.com as one site for common redirects."""
    host = (host or "").lower()
    bare = host[4:] if host.startswith("www.") else host
    return {bare, f"www.{bare}"}


def _fetch_robots(base_url: str) -> RobotFileParser:
    p = urlparse(base_url)
    robots_url = f"{p.scheme}://{p.netloc}/robots.txt"
    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        response = requests.get(robots_url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=False)
        if response.status_code == 200:
            parser.parse(response.text.splitlines())
        else:
            # A robots.txt 4xx response means no usable robots rules were supplied.
            # Continue with a low request rate; explicit rules in a 200 response are respected.
            parser.parse([])
    except requests.RequestException:
        # If robots.txt is unavailable due to a network error, use conservative rate limits.
        parser.parse([])
    return parser


def _url_score(url: str, anchor_text: str = "") -> int:
    candidate = f"{url} {anchor_text}".lower()
    return sum(5 if term in url.lower() else 2 for term in PRIORITY_TERMS if term in candidate)


def _is_candidate(url: str, allowed_hosts: set[str]) -> bool:
    p = urlparse(url)
    if not p.hostname or p.hostname.lower() not in allowed_hosts:
        return False
    lower = url.lower()
    if any(term in lower for term in SKIP_TERMS):
        return False
    if p.path.count("/") > 8:
        return False
    return True


def _parse_html(html: str, page_url: str) -> tuple[str, str, list[tuple[int, str]]]:
    soup = BeautifulSoup(html, "lxml")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    links: list[tuple[int, str]] = []
    for anchor in soup.find_all("a", href=True):
        raw = anchor.get("href", "").strip()
        if not raw or raw.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        absolute = normalize_url(urljoin(page_url, raw))
        if absolute:
            links.append((_url_score(absolute, anchor.get_text(" ", strip=True)), absolute))
    for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav", "aside", "form"]):
        tag.decompose()
    main = soup.find("main") or soup.find("article") or soup.body or soup
    text = " ".join(main.get_text(" ", strip=True).split())
    return title, text, links


def _render_with_playwright(url: str) -> tuple[str, str, list[tuple[int, str]]] | None:
    """Optional JS fallback. Returns None when Playwright is not installed or fails."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=USER_AGENT)
            page.goto(url, wait_until="domcontentloaded", timeout=TIMEOUT * 1000)
            try:
                page.wait_for_load_state("networkidle", timeout=5_000)
            except Exception:
                pass
            html = page.content()
            final_url = normalize_url(page.url) or url
            browser.close()
        return _parse_html(html, final_url)
    except Exception:
        return None


def _sitemap_urls(start_url: str, allowed_hosts: set[str], robots: RobotFileParser) -> list[str]:
    p = urlparse(start_url)
    candidates = [f"{p.scheme}://{p.netloc}/sitemap.xml", f"{p.scheme}://{p.netloc}/sitemap_index.xml"]
    try:
        robots_response = requests.get(
            f"{p.scheme}://{p.netloc}/robots.txt", headers=HEADERS,
            timeout=TIMEOUT, allow_redirects=False,
        )
        if robots_response.status_code == 200:
            for line in robots_response.text.splitlines():
                if line.lower().startswith("sitemap:"):
                    candidates.insert(0, line.split(":", 1)[1].strip())
    except requests.RequestException:
        pass
    urls: list[str] = []
    seen_maps: set[str] = set()
    while candidates and len(urls) < MAX_PAGES * 12:
        sitemap = candidates.pop(0)
        if sitemap in seen_maps:
            continue
        seen_maps.add(sitemap)
        try:
            sitemap = validate_public_url(sitemap)
            if not _is_candidate(sitemap, allowed_hosts) and (urlparse(sitemap).hostname or "").lower() not in allowed_hosts:
                continue
            response = requests.get(sitemap, headers=HEADERS, timeout=TIMEOUT, allow_redirects=False, stream=True)
            try:
                if response.status_code != 200 or len(response.content) > 2_000_000:
                    continue
                root = ET.fromstring(response.content)
            finally:
                response.close()
            for loc in root.iter():
                if not (loc.tag.lower().endswith("loc") and loc.text):
                    continue
                loc_url = normalize_url(loc.text)
                if not loc_url or not _is_candidate(loc_url, allowed_hosts):
                    continue
                if loc_url.endswith(".xml") and "sitemap" in loc_url.lower():
                    if len(seen_maps) < 8:
                        candidates.append(loc_url)
                elif robots.can_fetch(USER_AGENT, loc_url):
                    urls.append(loc_url)
        except (requests.RequestException, ValueError, ET.ParseError):
            continue
    return list(dict.fromkeys(urls))


def scrape_website(start_url: str) -> list[dict]:
    start_url = validate_public_url(str(start_url))
    start_parsed = urlparse(start_url)
    original_host = (start_parsed.hostname or "").lower()
    allowed_hosts = _host_aliases(original_host)
    robots = _fetch_robots(start_url)
    sitemap = sorted(_sitemap_urls(start_url, allowed_hosts, robots), key=lambda u: _url_score(u), reverse=True)
    queue: deque[str] = deque([start_url] + [u for u in sitemap if u != start_url])
    queued = set(queue)
    visited: set[str] = set()
    pages: list[dict] = []
    warnings: list[str] = []
    session = requests.Session()
    session.headers.update(HEADERS)
    js_fallback_used = False

    while queue and len(pages) < MAX_PAGES:
        url = normalize_url(queue.popleft())
        if not url or url in visited:
            continue
        visited.add(url)
        if not _is_candidate(url, allowed_hosts):
            continue
        if not robots.can_fetch(USER_AGENT, url):
            warnings.append(f"Blocked by robots.txt: {url}")
            continue
        response = None
        try:
            validate_public_url(url)
            response = session.get(url, timeout=TIMEOUT, allow_redirects=False, stream=True)
            if response.status_code in REDIRECT_CODES:
                location = response.headers.get("Location")
                if not location:
                    warnings.append(f"Redirect without a destination: {url}")
                    continue
                target = normalize_url(urljoin(url, location))
                target_host = (urlparse(target).hostname or "").lower()
                if target and target_host in allowed_hosts and target not in visited and target not in queued:
                    try:
                        validate_public_url(target)
                        queue.appendleft(target)
                        queued.add(target)
                    except ValueError as exc:
                        warnings.append(f"Unsafe redirect skipped ({exc}): {target}")
                else:
                    warnings.append(f"Redirect leaves the allowed site and was skipped: {url} -> {target}")
                continue
            if response.status_code != 200:
                warnings.append(f"HTTP {response.status_code}: {url}")
                continue
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                warnings.append(f"Skipped non-HTML content: {url}")
                continue
            content_length = response.headers.get("Content-Length", "")
            if content_length.isdigit() and int(content_length) > MAX_BYTES:
                warnings.append(f"Page too large: {url}")
                continue
            chunks, size = [], 0
            for chunk in response.iter_content(8192):
                if not chunk:
                    continue
                size += len(chunk)
                if size > MAX_BYTES:
                    break
                chunks.append(chunk)
            if size > MAX_BYTES:
                warnings.append(f"Page exceeded size limit: {url}")
                continue
            html = b"".join(chunks).decode(response.encoding or "utf-8", errors="replace")
            title, text, links = _parse_html(html, url)
            if len(text) < 100 and not js_fallback_used:
                rendered = _render_with_playwright(url)
                js_fallback_used = True
                if rendered:
                    rendered_title, rendered_text, rendered_links = rendered
                    if len(rendered_text) > len(text):
                        title, text, links = rendered_title or title, rendered_text, rendered_links or links
            if len(text) < 80:
                warnings.append(f"Very little readable text ({len(text)} characters): {url}")
                continue
            pages.append({"url": url, "title": title, "text": text[:60000]})
            for _score, link in sorted(links, key=lambda pair: pair[0], reverse=True):
                if _is_candidate(link, allowed_hosts) and link not in visited and link not in queued:
                    if len(queued) < MAX_PAGES * 30:
                        queue.append(link)
                        queued.add(link)
        except (requests.RequestException, ValueError) as exc:
            warnings.append(f"Failed to fetch {url}: {type(exc).__name__}: {exc}")
        finally:
            if response is not None:
                response.close()
        time.sleep(0.2)

    if not pages:
        if not warnings:
            warnings.append("No pages were eligible for crawling under the current site rules.")
        summary = "; ".join(warnings[:5])
        if len(warnings) > 5:
            summary += f"; and {len(warnings) - 5} more warning(s)"
        raise ValueError(
            "No readable pages were collected. Check whether the website allows crawling, "
            "redirects to another domain, requires JavaScript, or returns an access-denied response. "
            f"Crawler diagnostics: {summary}"
        )

    pages[0]["_crawl_warnings"] = warnings[:100]
    pages[0]["_discovered_url_count"] = len(visited) + len(queue)
    return pages
