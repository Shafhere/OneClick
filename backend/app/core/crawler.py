
import ipaddress
import socket
from collections import deque
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

load_dotenv()

MAX_PAGES = int(os.getenv("MAX_PAGES", "12"))
TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "15"))

HEADERS = {
    "User-Agent": "OneClickResearchBot/1.0"
}


def validate_public_url(url: str) -> str:
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Please provide a valid HTTP or HTTPS URL.")

    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not allowed.")

    host = parsed.hostname.lower()

    if host == "localhost" or host.endswith(".localhost"):
        raise ValueError("Local addresses cannot be crawled.")

    try:
        addresses = socket.getaddrinfo(host, None)
        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if not ip.is_global:
                raise ValueError("Private or non-public addresses cannot be crawled.")
    except socket.gaierror as exc:
        raise ValueError("The website hostname could not be resolved.") from exc

    return url


def get_robots_parser(base_url: str):
    parsed = urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    parser = RobotFileParser()
    parser.set_url(robots_url)

    try:
        response = requests.get(
            robots_url, headers=HEADERS, timeout=TIMEOUT
        )
        if response.status_code == 200:
            parser.parse(response.text.splitlines())
        else:
            parser.parse([])
    except requests.RequestException:
        # Fail closed if robots.txt cannot be checked.
        parser.parse(["User-agent: *", "Disallow: /"])

    return parser


def clean_page(html: str, page_url: str):
    soup = BeautifulSoup(html, "lxml")

    for tag in soup([
        "script", "style", "noscript", "svg",
        "header", "footer", "nav", "aside"
    ]):
        tag.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    text = soup.get_text(" ", strip=True)

    links = []
    for anchor in soup.find_all("a", href=True):
        absolute = urldefrag(urljoin(page_url, anchor["href"]))[0]
        parsed = urlparse(absolute)

        if parsed.scheme in ("http", "https"):
            links.append(absolute)

    return title, text, links


def scrape_website(start_url: str):
    start_url = validate_public_url(str(start_url))
    start = urlparse(start_url)
    allowed_host = start.hostname.lower()

    robots = get_robots_parser(start_url)
    queue = deque([start_url])
    visited = set()
    pages = []

    session = requests.Session()
    session.headers.update(HEADERS)

    while queue and len(pages) < MAX_PAGES:
        url = queue.popleft()
        url = urldefrag(url)[0]

        if url in visited:
            continue

        visited.add(url)

        parsed = urlparse(url)
        if parsed.hostname != allowed_host:
            continue

        if not robots.can_fetch(HEADERS["User-Agent"], url):
            continue

        try:
            # Revalidate every destination before making a request.
            validate_public_url(url)
            response = session.get(
                url,
                timeout=TIMEOUT,
                allow_redirects=False,
                stream=True,
            )

            if response.status_code in (301, 302, 303, 307, 308):
                continue

            if response.status_code != 200:
                continue

            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type.lower():
                continue

            # Avoid downloading excessively large pages.
            if int(response.headers.get("Content-Length", 0)) > 3_000_000:
                continue

            chunks = []
            size = 0

            for chunk in response.iter_content(8192):
                size += len(chunk)
                if size > 3_000_000:
                    break
                chunks.append(chunk)

            if size > 3_000_000:
                continue

            html = b"".join(chunks).decode(
                response.encoding or "utf-8", errors="replace"
            )
            title, text, links = clean_page(html, url)

            if len(text) < 100:
                continue

            pages.append({
                "url": url,
                "title": title,
                "text": text[:40000],
            })

            for link in links:
                link_parsed = urlparse(link)

                if (
                    link_parsed.hostname
                    and link_parsed.hostname.lower() == allowed_host
                    and link not in visited
                    and link not in queue
                    and len(queue) < MAX_PAGES * 10
                ):
                    queue.append(link)

        except (requests.RequestException, ValueError):
            continue
        finally:
            if "response" in locals():
                response.close()
                del response

    if not pages:
        raise ValueError(
            "No readable pages were collected. The site may block crawlers, "
            "disallow crawling, or require JavaScript."
        )

    return pages
