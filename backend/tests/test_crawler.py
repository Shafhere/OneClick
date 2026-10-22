from app.core.crawler import normalize_url, _parse_html, _url_score


def test_normalize_url_removes_fragment_and_tracking():
    assert normalize_url("https://Example.com/path/?utm_source=test#section") == "https://example.com/path"


def test_links_are_extracted_before_navigation_is_removed():
    html = """<html><head><title>Home</title></head><body>
    <nav><a href='/about'>About us</a><a href='/pricing'>Pricing</a></nav>
    <main><p>Company text that is long enough to be meaningful and read by the crawler.</p></main>
    </body></html>"""
    title, text, links = _parse_html(html, "https://example.com/")
    urls = [url for _score, url in links]
    assert title == "Home"
    assert "https://example.com/about" in urls
    assert "https://example.com/pricing" in urls
    assert "About us" not in text


def test_relevant_pages_rank_higher():
    assert _url_score("https://example.com/pricing") > _url_score("https://example.com/random-post")
