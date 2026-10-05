#!/usr/bin/env python3
"""Refresh a small, approved service-topic selection from genuine search trends.

Google's public RSS feed reports recent trending queries for individual markets;
it does not report this site's rankings or worldwide service-keyword volume.
US, GB, CA and AU are samples, not the studio's service-area restrictions.

Only catalogue labels and targets should be rendered in the website. Raw queries
are stored exclusively as provenance, never generated website copy. A topic is
eligible only when a complete approved phrase appears in a recent feed query.
No relevant observation is a valid empty result. Any incomplete/invalid fetch
leaves the previous snapshot unchanged and causes the CLI to exit unsuccessfully.
"""

import argparse
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import json
import os
from pathlib import Path
import re
import tempfile
import unicodedata
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "data" / "trend-topics.json"
DEFAULT_OUTPUT = ROOT / "data" / "seo-trends.json"
MARKETS = ("US", "GB", "CA", "AU")
SOURCE = "Google Trends RSS"
SOURCE_URLS = {
    market: "https://trends.google.com/trending/rss?geo=" + market
    for market in MARKETS
}
VALID_TARGETS = frozenset({
    "/branding", "/web-design", "/web-development", "/ui-ux-design",
    "/custom-software-development", "/ai-automation", "/creative-content",
    "/product-photography", "/seo",
})
MAX_FEED_BYTES = 1_000_000
TIMEOUT_SECONDS = 20
MAX_AGE = timedelta(days=7)
MAX_TOPICS = 6
FUTURE_TOLERANCE = timedelta(minutes=10)


class TrendRefreshError(ValueError):
    """Invalid trend data; never replace the last successful snapshot."""


def utc_now(now=None):
    value = now or datetime.now(timezone.utc)
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise TrendRefreshError("Trend timestamps must include a timezone")
    return value.astimezone(timezone.utc).replace(microsecond=0)


def timestamp(value):
    return utc_now(value).isoformat().replace("+00:00", "Z")


def normalized(value):
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.findall(r"[^\W_]+", value, flags=re.UNICODE))


def plain_text(value, label, maximum=160):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise TrendRefreshError(f"Invalid {label}")
    if any(ord(char) < 32 or char in "<>" for char in value):
        raise TrendRefreshError(f"Invalid characters in {label}")
    return value.strip()


def validate_catalog(catalog):
    if not isinstance(catalog, dict) or catalog.get("version") != 1:
        raise TrendRefreshError("Expected trend-topic catalogue version 1")
    topics = catalog.get("topics")
    if not isinstance(topics, list) or not 1 <= len(topics) <= 30:
        raise TrendRefreshError("Catalogue must contain approved topics")
    output, seen_ids, seen_aliases = [], set(), set()
    for topic in topics:
        if not isinstance(topic, dict):
            raise TrendRefreshError("Invalid catalogue topic")
        topic_id = plain_text(topic.get("id"), "topic id", 80)
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", topic_id) or topic_id in seen_ids:
            raise TrendRefreshError("Topic identifiers must be unique slugs")
        label = plain_text(topic.get("label"), "topic label", 100)
        target = topic.get("target")
        if not isinstance(target, str) or target not in VALID_TARGETS:
            raise TrendRefreshError("Topic target must be an existing service page")
        aliases = topic.get("aliases")
        if not isinstance(aliases, list) or not 1 <= len(aliases) <= 20:
            raise TrendRefreshError("A topic requires explicit approved phrases")
        checked_aliases = []
        for alias in aliases:
            alias = normalized(plain_text(alias, "topic alias", 100))
            if len(alias.split()) < 2 or alias in seen_aliases:
                raise TrendRefreshError("Aliases must be unique phrases of at least two words")
            checked_aliases.append(alias)
            seen_aliases.add(alias)
        seen_ids.add(topic_id)
        output.append({"id": topic_id, "label": label, "target": target, "aliases": checked_aliases})
    return output


def parse_feed(payload, market, now=None):
    """Parse one trusted-source RSS response into recent, validated observations."""
    current = utc_now(now)
    if market not in MARKETS:
        raise TrendRefreshError("Unsupported feed market")
    if not isinstance(payload, bytes) or not payload or len(payload) > MAX_FEED_BYTES:
        raise TrendRefreshError(f"Invalid feed size for {market}")
    if b"<!DOCTYPE" in payload.upper() or b"<!ENTITY" in payload.upper():
        raise TrendRefreshError("XML declarations with entities are unsupported")
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as error:
        raise TrendRefreshError(f"Invalid RSS XML for {market}") from error
    channel = root.find("channel")
    if root.tag != "rss" or channel is None:
        raise TrendRefreshError(f"Expected Google Trends RSS for {market}")
    source_link = channel.findtext("link", "").strip()
    if source_link != SOURCE_URLS[market]:
        raise TrendRefreshError(f"Feed market/source mismatch for {market}")
    items = channel.findall("item")
    if len(items) > 500:
        raise TrendRefreshError("Unexpected RSS item count")
    observations = []
    for item in items:
        query = plain_text(item.findtext("title"), "feed query")
        try:
            published = parsedate_to_datetime(item.findtext("pubDate", ""))
            if published.tzinfo is None:
                raise ValueError("Missing timezone")
            published = utc_now(published)
        except (TypeError, ValueError, OverflowError) as error:
            raise TrendRefreshError(f"Invalid RSS publication date for {market}") from error
        if published > current + FUTURE_TOLERANCE:
            raise TrendRefreshError(f"Unexpected future publication date for {market}")
        if published < current - MAX_AGE:
            continue
        observations.append({
            "query": query,
            "market": market,
            "observed_at": timestamp(published),
            "source_url": SOURCE_URLS[market],
        })
    return observations


def select_topics(catalog, observations, now=None, max_topics=MAX_TOPICS):
    """Map recent observations to fixed catalogue fields; never generate copy."""
    current = utc_now(now)
    approved = validate_catalog(catalog)
    if type(max_topics) is not int or not 0 <= max_topics <= MAX_TOPICS:
        raise TrendRefreshError("At most six trend topics are permitted")
    if not isinstance(observations, list):
        raise TrendRefreshError("Observations must be a list")
    checked = []
    for observation in observations:
        if not isinstance(observation, dict):
            raise TrendRefreshError("Invalid trend observation")
        query = plain_text(observation.get("query"), "observed query")
        market = observation.get("market")
        if market not in MARKETS or observation.get("source_url") != SOURCE_URLS[market]:
            raise TrendRefreshError("Observation has an unapproved source")
        try:
            published = utc_now(datetime.fromisoformat(observation["observed_at"].replace("Z", "+00:00")))
        except (KeyError, AttributeError, TypeError, ValueError, OverflowError) as error:
            raise TrendRefreshError("Invalid observation timestamp") from error
        if published > current + FUTURE_TOLERANCE:
            raise TrendRefreshError("Observation date is in the future")
        if published >= current - MAX_AGE:
            checked.append({**observation, "query": query, "published": published})
    selected = []
    for topic in approved:
        matches = [
            observation for observation in checked
            if any(" " + alias + " " in " " + normalized(observation["query"]) + " "
                   for alias in topic["aliases"])
        ]
        if not matches:
            continue
        matches.sort(key=lambda item: (-item["published"].timestamp(), item["query"], item["market"]))
        newest = matches[0]
        markets = [market for market in MARKETS if any(item["market"] == market for item in matches)]
        selected.append({
            "id": topic["id"],
            "label": topic["label"],
            "target": topic["target"],
            "matched_query": newest["query"],
            "markets": markets,
            "observed_at": timestamp(newest["published"]),
            "source_urls": [SOURCE_URLS[market] for market in markets],
        })
    selected.sort(key=lambda item: (-len(item["markets"]), -datetime.fromisoformat(item["observed_at"].replace("Z", "+00:00")).timestamp(), item["id"]))
    return selected[:max_topics]


def build_snapshot(catalog, observations, now=None):
    current = utc_now(now)
    topics = select_topics(catalog, observations, current)
    return {
        "version": 1,
        "checked_at": timestamp(current),
        "source": SOURCE,
        "markets": list(MARKETS),
        "status": "ok" if topics else "no_relevant_trends",
        "topics": topics,
    }


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise TrendRefreshError("Unexpected redirect from an approved trend source")


def fetch_feed(market):
    if market not in MARKETS:
        raise TrendRefreshError("Unsupported feed market")
    request = urllib.request.Request(SOURCE_URLS[market], headers={
        "User-Agent": "VisionCraftLabsTrendMonitor/1.0 (+https://visioncraft-labs.com)",
        "Accept": "application/rss+xml, application/xml, text/xml",
    })
    try:
        opener = urllib.request.build_opener(NoRedirects())
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            if response.status != 200:
                raise TrendRefreshError(f"Trend source returned HTTP {response.status} for {market}")
            payload = response.read(MAX_FEED_BYTES + 1)
            if len(payload) > MAX_FEED_BYTES:
                raise TrendRefreshError(f"Trend source exceeded the size limit for {market}")
            return payload
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise TrendRefreshError(f"Could not fetch trend source for {market}: {type(error).__name__}") from error


def atomic_write(output_path, snapshot):
    """Serialize completely, then replace within the same filesystem directory."""
    encoded = json.dumps(snapshot, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    output_path = Path(output_path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output_path.parent,
                                         prefix=".seo-trends-", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output_path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def refresh_trends(catalog_path=DEFAULT_CATALOG, output_path=DEFAULT_OUTPUT, now=None, fetcher=fetch_feed):
    """Require all four valid feeds before atomically saving a new snapshot."""
    current = utc_now(now)
    try:
        catalog = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise TrendRefreshError("Could not read the approved topic catalogue") from error
    validate_catalog(catalog)
    observations = []
    for market in MARKETS:
        try:
            payload = fetcher(market)
            observations.extend(parse_feed(payload, market, current))
        except Exception as error:
            raise TrendRefreshError(f"Refresh aborted for {market}; the previous snapshot is unchanged: {error}") from error
    snapshot = build_snapshot(catalog, observations, current)
    atomic_write(output_path, snapshot)
    return snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    try:
        snapshot = refresh_trends(arguments.catalog, arguments.output)
    except (TrendRefreshError, OSError) as error:
        parser.exit(1, f"Trend refresh failed: {error}\n")
    print(f"Trend refresh: {len(snapshot['topics'])} approved topics; {snapshot['status']}; "
          f"all {len(MARKETS)} market feeds verified at {snapshot['checked_at']}")


if __name__ == "__main__":
    main()
