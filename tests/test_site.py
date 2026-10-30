from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
BASE = urlsplit("https://sal0-h.github.io/feurtube/")


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.ids = []
        self.references = []
        self.versions = {}
        self.feed(path.read_text())

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        for name in ("href", "src"):
            if attrs.get(name):
                self.references.append(attrs[name])
        if tag == "meta" and attrs.get("property") == "og:image":
            self.references.append(attrs["content"])
        if "data-youtube-version" in attrs:
            self.versions[attrs["data-youtube-version"]] = attrs.get("data-experimental")


class SiteTests(unittest.TestCase):
    def setUp(self):
        self.pages = {p.resolve(): Page(p) for p in SITE.glob("*.html")}

    def local_target(self, source, reference):
        parts = urlsplit(reference)
        if parts.netloc and parts.netloc != BASE.netloc:
            return None
        if parts.scheme and parts.scheme not in ("http", "https"):
            return None
        path = unquote(parts.path)
        if path.startswith("/"):
            self.assertTrue(path.startswith(BASE.path), reference)
            target = SITE / path.removeprefix(BASE.path)
        else:
            target = source.parent / (path or source.name)
        target = target.resolve()
        if target.is_dir():
            target /= "index.html"
        self.assertTrue(target.is_relative_to(SITE.resolve()), reference)
        self.assertTrue(target.is_file(), f"Broken reference in {source.name}: {reference}")
        if parts.fragment:
            self.assertIn(target, self.pages, reference)
            self.assertIn(unquote(parts.fragment), self.pages[target].ids, reference)
        return target

    def test_local_links_assets_and_fragment_targets(self):
        for path, page in self.pages.items():
            with self.subTest(page=path.name):
                self.assertEqual(len(page.ids), len(set(page.ids)), "Duplicate HTML IDs")
                for reference in page.references:
                    self.local_target(path, reference)
        for path in (SITE / "assets").glob("*.css"):
            for reference in re.findall(r'url\([\s\'"]*([^\)\'"\s]+)', path.read_text()):
                self.local_target(path, reference)

    def test_documented_versions_match_the_patcher(self):
        lock = json.loads((ROOT / "upstream.lock.json").read_text())
        versions = set(lock["youtube"]["versions"])
        experimental = set(lock["youtube"]["experimental"])
        guide = self.pages[(SITE / "guide.html").resolve()]
        self.assertEqual(set(guide.versions), versions)
        for version, status in guide.versions.items():
            self.assertEqual(status, str(version in experimental).lower(), version)
        for path, page in self.pages.items():
            self.assertLessEqual(set(page.versions), versions, path.name)

    def test_sitemap_points_to_existing_pages(self):
        sitemap = ET.parse(SITE / "sitemap.xml")
        urls = [node.text for node in sitemap.findall("{*}url/{*}loc")]
        self.assertEqual(len(urls), len(set(urls)))
        for url in urls:
            self.assertIn(self.local_target(SITE / "index.html", url), self.pages)


if __name__ == "__main__":
    unittest.main()
