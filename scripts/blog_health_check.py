import json
import sys
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

BASE = "https://satyaprakashprajapatizz-ai.github.io/digital-products-public/"
SITEMAP = urllib.parse.urljoin(BASE, "sitemap.xml")

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.in_title = False
        self.has_jsonld = False
    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True
        if tag == "script":
            if dict(attrs).get("type") == "application/ld+json":
                self.has_jsonld = True
    def handle_data(self, data):
        if self.in_title:
            self.title += data
    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "BlogHealthCheck/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status, r.read()

def main():
    status, body = fetch(SITEMAP)
    if status != 200:
        raise RuntimeError(f"sitemap returned {status}")
    root = ET.fromstring(body)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [x.text.strip() for x in root.findall(".//sm:loc", ns) if x.text]
    if not urls:
        raise RuntimeError("sitemap contains no URLs")
    failures = []
    reports = []
    for url in urls:
        try:
            code, content = fetch(url)
            if code != 200:
                raise RuntimeError(f"HTTP {code}")
            if url.endswith(".xml"):
                reports.append({"url": url, "status": code})
                continue
            parser = PageParser()
            parser.feed(content.decode("utf-8", errors="replace"))
            if not parser.title.strip():
                raise RuntimeError("missing <title>")
            reports.append({"url": url, "status": code, "title": parser.title.strip(), "jsonld": parser.has_jsonld})
        except Exception as exc:
            failures.append({"url": url, "error": str(exc)})
    print(json.dumps({"checked": len(urls), "passed": len(reports), "failures": failures}, indent=2))
    if failures:
        sys.exit(1)

if __name__ == "__main__":
    main()
