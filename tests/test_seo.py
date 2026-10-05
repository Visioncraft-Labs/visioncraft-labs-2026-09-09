"""SEO contracts: editorial copy, constrained trends and atomic refreshes."""
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from seo import load_keywords, trend_links
from refresh_trends import (
    MARKETS, SOURCE_URLS, TrendRefreshError, build_snapshot, parse_feed,
    refresh_trends, select_topics, validate_catalog,
)

NOW = datetime(2026, 10, 4, 12, tzinfo=timezone.utc)


class KeywordCopyTests(unittest.TestCase):
    def test_global_copy_covers_all_services_without_rank_claims(self):
        services = json.loads((ROOT / "data/services.json").read_text())
        entries = load_keywords(ROOT / "data/keyword-map.json", services)
        self.assertEqual(len(entries), 9)
        self.assertEqual(set(entries), {"/" + service["slug"] for service in services})
        self.assertEqual(len({entry["seo_title"] for entry in entries.values()}), 9)
        self.assertEqual(len({entry["meta_description"] for entry in entries.values()}), 9)
        for entry in entries.values():
            with self.subTest(service=entry["target"]):
                self.assertNotIn("pakistan", json.dumps(entry).lower())
                self.assertIn(entry["primary"].lower(), entry["intro"].lower())
                self.assertLessEqual(len(entry["seo_title"]), 65)
                self.assertTrue(140 <= len(entry["meta_description"]) <= 165)
                self.assertIn("have not been measured", entry["validation"])
                self.assertTrue(2 <= len(entry["topics"]) <= 4)

    def test_missing_service_map_fails_instead_of_silently_losing_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "keywords.json"
            path.write_text("[]")
            with self.assertRaises(ValueError):
                load_keywords(path, [{"slug": "web-design"}])


class TrendRenderingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "data").mkdir()
        self.write("services.json", [{"slug": "web-design"}, {"slug": "ai-automation"}])
        self.write("trend-topics.json", {"topics": [
            {"id": "responsive-design", "target": "/web-design", "label": "Responsive & accessible design"},
            {"id": "bad-path", "target": "https://untrusted.example/", "label": "Must never appear"},
            {"id": "safe-label", "target": "/ai-automation", "label": '<img src=x onerror="alert(1)">'},
        ]})

    def write(self, name, data):
        (self.root / "data" / name).write_text(json.dumps(data))

    def observation(self, identity="responsive-design", date=NOW):
        return {"id": identity, "observed_at": date.isoformat(),
                "query": '<script>alert("rss")</script>',
                "label": "REMOTE TEXT MUST NOT APPEAR", "target": "javascript:alert(2)"}

    def test_only_approved_labels_and_service_paths_are_rendered(self):
        self.write("seo-trends.json", {"topics": [
            self.observation(), self.observation(), self.observation("unapproved"),
            self.observation("bad-path"), self.observation("safe-label"),
        ]})
        output = trend_links(self.root, now=NOW)
        self.assertEqual(output.count('href="web-design.html"'), 1)
        self.assertIn("Responsive &amp; accessible design", output)
        self.assertIn("&lt;img", output)
        for forbidden in ("<script", "<img", "REMOTE TEXT", "javascript:", "untrusted.example", "Must never appear"):
            self.assertNotIn(forbidden, output)

    def test_stale_future_and_invalid_dates_never_reach_public_copy(self):
        entries = [self.observation(date=NOW - timedelta(days=8)),
                   self.observation(date=NOW + timedelta(days=1)),
                   self.observation()]
        entries[-1]["observed_at"] = "not-a-date"
        self.write("seo-trends.json", {"topics": entries})
        self.assertEqual(trend_links(self.root, now=NOW), "")


class TrendRefreshTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.catalog = {"version": 1, "topics": [
            {"id": "web-design", "label": "Responsive website design", "target": "/web-design",
             "aliases": ["responsive design", "web design"]},
            {"id": "ai-automation", "label": "AI and workflow automation", "target": "/ai-automation",
             "aliases": ["ai automation", "workflow automation"]},
        ]}
        self.catalog_path = self.root / "catalog.json"
        self.catalog_path.write_text(json.dumps(self.catalog))
        self.output_path = self.root / "snapshot.json"
        self.old_bytes = b'{"version":1,"topics":[],"last_success":"keep exactly"}\n'
        self.output_path.write_bytes(self.old_bytes)

    def observation(self, query, date=NOW, market="US"):
        return {"query": query, "observed_at": date.isoformat(), "market": market,
                "source_url": SOURCE_URLS[market]}

    def feed(self, market, query="Premier league scores", date=NOW):
        return ('<?xml version="1.0"?><rss version="2.0"><channel>'
                f'<title>Daily Search Trends</title><link>{escape(SOURCE_URLS[market])}</link>'
                f'<item><title>{escape(query)}</title><pubDate>{format_datetime(date)}</pubDate>'
                '</item></channel></rss>').encode()

    def test_catalog_is_constrained_and_rejects_ambiguous_single_words(self):
        production = json.loads((ROOT / "data/trend-topics.json").read_text())
        self.assertEqual(len(validate_catalog(production)), 9)
        self.catalog["topics"][1]["aliases"] = ["AI"]
        with self.assertRaises(TrendRefreshError):
            validate_catalog(self.catalog)

    def test_phrase_match_handles_case_punctuation_and_complete_word_boundaries(self):
        matches = select_topics(self.catalog, [self.observation("New: RESPONSIVE—DESIGN tools")], now=NOW)
        self.assertEqual([entry["id"] for entry in matches], ["web-design"])
        self.assertEqual(matches[0]["label"], "Responsive website design")
        self.assertEqual(matches[0]["target"], "/web-design")
        for query in ("web designer awards", "responsive designs", "ai automations"):
            with self.subTest(query=query):
                self.assertEqual(select_topics(self.catalog, [self.observation(query)], now=NOW), [])

    def test_unrelated_news_and_ambiguous_ai_never_become_service_trends(self):
        unrelated = ["World cup final", "AI", "OpenAI earnings", "Apple launch", "election results"]
        result = build_snapshot(self.catalog, [self.observation(query) for query in unrelated], now=NOW)
        self.assertEqual(result["topics"], [])
        self.assertEqual(result["status"], "no_relevant_trends")

    def test_stale_observations_are_excluded_and_future_dates_are_rejected(self):
        stale = NOW - timedelta(days=8)
        future = NOW + timedelta(days=1)
        self.assertEqual(parse_feed(self.feed("US", "web design", stale), "US", now=NOW), [])
        self.assertEqual(select_topics(self.catalog, [self.observation("web design", stale)], now=NOW), [])
        with self.assertRaises(TrendRefreshError):
            parse_feed(self.feed("US", "web design", future), "US", now=NOW)
        with self.assertRaises(TrendRefreshError):
            select_topics(self.catalog, [self.observation("web design", future)], now=NOW)

    def test_malformed_or_partially_failed_feed_preserves_previous_snapshot_bytes(self):
        for failure in ("malformed", "network", "wrong-market"):
            with self.subTest(failure=failure):
                calls = []

                def fetcher(market):
                    calls.append(market)
                    if market == "CA":
                        if failure == "network":
                            raise TimeoutError("fixture timeout")
                        if failure == "malformed":
                            return b"<rss><broken>"
                        return self.feed("US", "web design")
                    return self.feed(market, "web design")

                with self.assertRaises(TrendRefreshError):
                    refresh_trends(self.catalog_path, self.output_path, now=NOW, fetcher=fetcher)
                self.assertEqual(calls[:2], ["US", "GB"])
                self.assertEqual(self.output_path.read_bytes(), self.old_bytes)

    def test_successful_refresh_requires_all_four_feeds_and_writes_valid_empty_snapshot(self):
        calls = []

        def fetcher(market):
            calls.append(market)
            return self.feed(market)

        result = refresh_trends(self.catalog_path, self.output_path, now=NOW, fetcher=fetcher)
        self.assertEqual(calls, ["US", "GB", "CA", "AU"])
        self.assertEqual(json.loads(self.output_path.read_text()), result)
        self.assertEqual(result["topics"], [])
        self.assertEqual(result["status"], "no_relevant_trends")
        self.assertEqual(set(result["markets"]), set(MARKETS))

    def test_successful_refresh_preserves_source_evidence_without_generating_copy(self):
        result = refresh_trends(
            self.catalog_path, self.output_path, now=NOW,
            fetcher=lambda market: self.feed(market, "RESPONSIVE DESIGN tutorial"),
        )
        self.assertEqual(json.loads(self.output_path.read_text()), result)
        self.assertEqual(len(result["topics"]), 1)
        topic = result["topics"][0]
        self.assertEqual(topic["label"], "Responsive website design")
        self.assertEqual(topic["target"], "/web-design")
        self.assertEqual(topic["matched_query"], "RESPONSIVE DESIGN tutorial")
        self.assertEqual(set(topic["source_urls"]), set(SOURCE_URLS.values()))

    def test_failed_final_replace_leaves_previous_file_readable_and_unchanged(self):
        with patch("refresh_trends.os.replace", side_effect=OSError("fixture disk failure")):
            with self.assertRaises(OSError):
                refresh_trends(self.catalog_path, self.output_path, now=NOW,
                               fetcher=lambda market: self.feed(market, "web design"))
        self.assertEqual(self.output_path.read_bytes(), self.old_bytes)
        self.assertEqual(list(self.root.glob(".seo-trends-*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
