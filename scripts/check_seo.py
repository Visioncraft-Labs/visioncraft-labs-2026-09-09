"""Fail a build when its public crawl settings disagree with the deploy mode."""

import argparse
from collections import Counter
from html.parser import HTMLParser
import os
from pathlib import Path
import re
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET


DEFAULT_ORIGIN = "https://visioncraft-labs.com"
NOINDEX_FILES = {"404.html", "thank-you.html"}
ROBOT_META_NAMES = {"robots", "googlebot", "googlebot-news", "bingbot", "slurp", "yandex", "duckduckbot", "baiduspider"}


def directives(value):
    result = set(re.split(r"[\s,]+", value.strip().lower()))
    if "none" in result:
        result.update(("noindex", "nofollow"))
    if "all" in result:
        result.update(("index", "follow"))
    return result


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.titles = []
        self.in_title = False
        self.descriptions = []
        self.canonicals = []
        self.robots = []

    def handle_starttag(self, tag, attrs):
        attrs = {key: value or "" for key, value in attrs}
        if tag == "title":
            self.titles.append("")
            self.in_title = True
        if tag == "meta":
            name = attrs.get("name", "").lower()
            content = attrs.get("content", "")
            if name == "description":
                self.descriptions.append(content.strip())
            if name in ROBOT_META_NAMES:
                self.robots.append((name, content))
        if tag == "link" and "canonical" in attrs.get("rel", "").lower().split():
            self.canonicals.append(attrs.get("href", "").strip())

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, value):
        if self.in_title:
            self.titles[-1] += value


def page_path(relative_path):
    if relative_path.name == "index.html":
        parent = relative_path.parent.as_posix()
        return "/" if parent == "." else "/" + parent + "/"
    return "/" + relative_path.with_suffix("").as_posix()


def robot_groups(text):
    """Parse groups without relying on blank lines or directive capitalization."""
    groups = []
    agents, rules = [], []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        key = key.lower()
        if key == "user-agent":
            if rules:
                groups.append((agents, rules))
                agents, rules = [], []
            agents.append(value.lower())
        elif key in ("allow", "disallow") and agents:
            rules.append((key, value))
    if agents:
        groups.append((agents, rules))
    return groups


def robots_allows(path, rules):
    matches = []
    for action, pattern in rules:
        if not pattern:
            continue
        expression = re.escape(pattern).replace(r"\*", ".*")
        if pattern.endswith("$"):
            expression = expression[:-2] + "$"
        if re.match(expression, path):
            specificity = len(pattern.replace("*", "").rstrip("$"))
            matches.append((specificity, action == "allow"))
    return max(matches)[1] if matches else True


def header_rules(text):
    pattern = None
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not raw[0].isspace():
            pattern = stripped
        elif ":" in stripped:
            name, value = stripped.split(":", 1)
            if name.strip().lower() == "x-robots-tag":
                yield pattern, value.strip()


def header_matches(pattern, path):
    if not pattern:
        return False
    # Netlify accepts splats and named path segments in header rules.
    expression = re.escape(pattern).replace(r"\*", ".*")
    expression = re.sub(r":\w+", "[^/]+", expression)
    return re.fullmatch(expression, path) is not None


def check(dist, mode="preview", origin=DEFAULT_ORIGIN):
    dist = Path(dist)
    origin = origin.rstrip("/")
    preview = mode != "production"
    errors = []
    origin_parts = urlsplit(origin)
    if origin_parts.scheme not in ("http", "https") or not origin_parts.netloc or origin_parts.query or origin_parts.fragment:
        return ["SITE_URL must be an absolute HTTP(S) origin without a query or fragment."]
    pages = {}
    expected_urls = set()
    indexable_paths = set()
    all_paths = set()
    for path in sorted(dist.rglob("*.html")):
        relative = path.relative_to(dist)
        if relative.parts[0] == "admin":
            continue
        label = relative.as_posix()
        page = Page()
        page.feed(path.read_text(encoding="utf-8"))
        pages[label] = page
        route = page_path(relative)
        aliases = {route, "/" + label}
        all_paths.update(aliases)
        excluded = label in NOINDEX_FILES
        if not excluded:
            expected_urls.add(origin + route)
            indexable_paths.update(aliases)
        if len(page.titles) != 1 or not page.titles[0].strip():
            errors.append(f"{label}: expected one nonempty title.")
        if len(page.descriptions) != 1 or not page.descriptions[0]:
            errors.append(f"{label}: expected one nonempty meta description.")
        if page.canonicals != [origin + route]:
            errors.append(f"{label}: canonical must be {origin + route}.")
        general = [directives(content) for name, content in page.robots if name == "robots"]
        required = {"noindex", "nofollow"} if preview or excluded else {"index", "follow"}
        if len(general) != 1 or not required.issubset(general[0]):
            errors.append(f"{label}: expected one robots meta containing {', '.join(sorted(required))}.")
        for name, content in page.robots:
            parsed = directives(content)
            forbidden = {"index", "follow"} if preview or excluded else {"noindex", "nofollow", "noimageindex"}
            if parsed & forbidden:
                errors.append(f"{label}: conflicting or blocking {name} meta: {content}.")

    if not pages:
        errors.append(f"No public HTML pages found in {dist}.")
    for field, label in (("titles", "title"), ("descriptions", "meta description")):
        values = [" ".join(value.split()).casefold() for page in pages.values() for value in getattr(page, field) if value.strip()]
        for value, count in Counter(values).items():
            if count > 1:
                errors.append(f"Duplicate {label} on {count} public pages: {value}.")

    robots_file = dist / "robots.txt"
    if not robots_file.is_file():
        errors.append("robots.txt is missing.")
    else:
        text = robots_file.read_text(encoding="utf-8")
        groups = robot_groups(text)
        wildcard = [rule for agents, rules in groups if "*" in agents for rule in rules]
        required_rule = ("disallow" if preview else "allow", "/")
        if required_rule not in wildcard:
            errors.append(f"robots.txt: User-agent: * must include {required_rule[0].title()}: / in {mode} mode.")
        # Check every explicit bot group too: a bot-specific group can override *.
        for agents, rules in groups:
            for route in sorted(all_paths if preview else indexable_paths):
                allowed = robots_allows(route, rules)
                if allowed == preview:
                    expectation = "block" if preview else "allow"
                    errors.append(f"robots.txt: group {', '.join(agents)} must {expectation} {route}.")
                    break
        if not preview:
            sitemap_declarations = [line.split(":", 1)[1].strip() for line in text.splitlines() if line.strip().lower().startswith("sitemap:")]
            if origin + "/sitemap.xml" not in sitemap_declarations:
                errors.append("robots.txt: missing the production sitemap URL.")

    sitemap_file = dist / "sitemap.xml"
    try:
        root = ET.parse(sitemap_file).getroot()
        if root.tag.rsplit("}", 1)[-1] != "urlset":
            errors.append("sitemap.xml: expected a urlset document.")
        urls = [(node.text or "").strip() for node in root.findall("./{*}url/{*}loc")]
        target = set() if preview else expected_urls
        if len(urls) != len(set(urls)):
            errors.append("sitemap.xml: duplicate URLs found.")
        if set(urls) != target:
            missing, extra = sorted(target - set(urls)), sorted(set(urls) - target)
            errors.append(f"sitemap.xml: expected exactly {len(target)} indexable URLs; missing={missing}, unexpected={extra}.")
    except (OSError, ET.ParseError) as exc:
        errors.append(f"sitemap.xml: cannot read valid XML: {exc}.")

    headers_file = dist / "_headers"
    if not preview and headers_file.is_file():
        for pattern, value in header_rules(headers_file.read_text(encoding="utf-8")):
            # A named bot prefix does not make a blocking header safe.
            parsed = directives(value.split(":", 1)[-1])
            if parsed & {"noindex", "nofollow", "noimageindex"}:
                affected = next((route for route in sorted(indexable_paths) if header_matches(pattern, route)), None)
                if affected:
                    errors.append(f"_headers: {pattern} sends blocking X-Robots-Tag to {affected}: {value}.")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=Path(__file__).resolve().parents[1] / "dist")
    parser.add_argument("--mode", default=os.environ.get("SITE_MODE", "preview"))
    parser.add_argument("--origin", default=os.environ.get("SITE_URL", DEFAULT_ORIGIN))
    args = parser.parse_args()
    errors = check(args.dist, args.mode, args.origin)
    if errors:
        print("SEO crawl guard failed:")
        for error in errors:
            print("- " + error)
        return 1
    print(f"PASS: {args.mode} canonical URLs, metadata, robots rules, sitemap coverage and public crawl headers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
