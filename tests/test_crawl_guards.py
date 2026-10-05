import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_seo", ROOT / "scripts/check_seo.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
ORIGIN = "https://example.test"


class CrawlGuards(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dist = Path(self.temp.name)
        self.fixture()

    def tearDown(self):
        self.temp.cleanup()

    def page(self, filename, robots="index, follow", extra=""):
        route = guard.page_path(Path(filename))
        path = self.dist / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'<html><head><title>{filename} title</title><meta name="description" content="Description for {filename}"><link rel="canonical" href="{ORIGIN}{route}"><meta name="robots" content="{robots}">{extra}</head><body></body></html>')

    def sitemap(self, routes):
        (self.dist / "sitemap.xml").write_text('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{ORIGIN}{route}</loc></url>' for route in routes) + '</urlset>')

    def fixture(self, mode="production"):
        for filename in ("index.html", "services.html", "404.html", "thank-you.html"):
            robots = "noindex, nofollow" if mode == "preview" or filename in guard.NOINDEX_FILES else "index, follow"
            self.page(filename, robots)
        self.page("admin/index.html", "noindex, nofollow")
        (self.dist / "robots.txt").write_text("User-agent: *\n" + ("Disallow: /\n" if mode == "preview" else f"Allow: /\nSitemap: {ORIGIN}/sitemap.xml\n"))
        (self.dist / "_headers").write_text("/*\n  X-Content-Type-Options: nosniff\n/admin/*\n  X-Robots-Tag: noindex, nofollow\n")
        self.sitemap([] if mode == "preview" else ["/", "/services"])

    def check(self, mode="production"):
        return guard.check(self.dist, mode, ORIGIN)

    def test_valid_production_and_private_preview(self):
        self.assertEqual(self.check(), [])
        self.fixture("preview")
        self.assertEqual(self.check("preview"), [])

    def test_future_pages_must_be_in_sitemap_and_noindex_pages_must_not(self):
        self.page("future-service.html")
        self.assertTrue(any("missing=" in error and "/future-service" in error for error in self.check()))
        self.sitemap(["/", "/services", "/future-service", "/thank-you"])
        self.assertTrue(any("unexpected=" in error and "/thank-you" in error for error in self.check()))
        self.sitemap(["/", "/services", "/future-service"])
        self.assertEqual(self.check(), [])

    def test_rejects_bot_specific_meta_and_conflicting_general_meta(self):
        for extra in ('<meta name="googlebot" content="noindex">', '<meta name="robots" content="none">'):
            with self.subTest(extra=extra):
                self.page("index.html", extra=extra)
                self.assertTrue(any("blocking" in error for error in self.check()))

    def test_bot_specific_robots_rule_cannot_block_public_route(self):
        with (self.dist / "robots.txt").open("a") as out:
            out.write("\nUser-agent: Googlebot\nDisallow: /services$\n")
        self.assertTrue(any("googlebot must allow /services" in error for error in self.check()))

    def test_public_header_blocks_are_rejected_but_admin_is_allowed(self):
        self.assertEqual(self.check(), [])
        for pattern in ("/*", "/services", "/services.html", "/:page"):
            with self.subTest(pattern=pattern):
                (self.dist / "_headers").write_text(f"{pattern}\n  X-Robots-Tag: googlebot: none\n")
                self.assertTrue(any("blocking X-Robots-Tag" in error for error in self.check()))

    def test_missing_and_duplicate_metadata_and_wrong_canonical(self):
        path = self.dist / "services.html"
        text = path.read_text().replace("services.html title", "index.html title").replace("Description for services.html", "Description for index.html").replace(ORIGIN + "/services", ORIGIN + "/wrong")
        path.write_text(text)
        errors = self.check()
        for expected in ("Duplicate title", "Duplicate meta description", "canonical must be"):
            self.assertTrue(any(expected in error for error in errors), errors)
        path.write_text(text.replace('<meta name="description" content="Description for index.html">', ""))
        self.assertTrue(any("nonempty meta description" in error for error in self.check()))

    def test_preview_rejects_indexable_metadata_sitemap_and_bot_override(self):
        self.fixture("preview")
        self.page("index.html")
        self.sitemap(["/"])
        with (self.dist / "robots.txt").open("a") as out:
            out.write("\nUser-agent: Googlebot\nAllow: /\n")
        errors = self.check("preview")
        for expected in ("expected one robots meta", "exactly 0 indexable URLs", "googlebot must block"):
            self.assertTrue(any(expected in error for error in errors), errors)

    def test_robots_longest_match_and_allow_tie(self):
        rules = [("allow", "/"), ("disallow", "/services"), ("allow", "/services/public")]
        self.assertFalse(guard.robots_allows("/services", rules))
        self.assertTrue(guard.robots_allows("/services/public", rules))
        self.assertTrue(guard.robots_allows("/", [("disallow", "/"), ("allow", "/")]))


if __name__ == "__main__":
    unittest.main()
