"""Stable editorial SEO and a strictly curated, server-rendered trend feature."""
import html
import json
from datetime import datetime, timezone, timedelta


def load_keywords(path, services):
    entries = json.loads(path.read_text())
    expected = {'/' + service['slug'] for service in services}
    result = {}
    for entry in entries:
        target = entry['target']
        if target not in expected or target in result:
            raise ValueError('Keyword map must have one entry per service')
        for key in ('primary', 'seo_title', 'meta_description', 'intro'):
            if not isinstance(entry.get(key), str) or not entry[key].strip():
                raise ValueError(f'Missing {key} for {target}')
        result[target] = entry
    if set(result) != expected:
        raise ValueError('Keyword map does not cover every service')
    return result


def trend_links(root, now=None):
    """Only render approved catalog labels/paths, never text received from RSS."""
    now = now or datetime.now(timezone.utc)
    snapshot = json.loads((root / 'data/seo-trends.json').read_text())
    catalog = json.loads((root / 'data/trend-topics.json').read_text())
    catalog = catalog['topics'] if isinstance(catalog, dict) else catalog
    approved = {item['id']: item for item in catalog}
    service_paths = {'/' + item['slug'] for item in json.loads((root / 'data/services.json').read_text())}
    chosen = []
    seen = set()
    for observed in snapshot.get('topics', []):
        entry = approved.get(observed.get('id'))
        if not entry or entry['target'] not in service_paths or entry['id'] in seen:
            continue
        try:
            date = datetime.fromisoformat(observed['observed_at'].replace('Z', '+00:00'))
            if date.tzinfo is None or not now - timedelta(days=7) <= date <= now + timedelta(hours=1):
                continue
        except (ValueError, KeyError, TypeError):
            continue
        seen.add(entry['id'])
        chosen.append(entry)
    if not chosen:
        return ''
    links = ''.join(f'<a href="{html.escape(item["target"].lstrip("/"))}.html">{html.escape(item["label"])}</a>' for item in chosen[:6])
    return '<section class="related-band"><div class="wrap"><span class="eyebrow">In focus</span><h2>Ideas for your next project.</h2><p>Explore capabilities connected to current search interest.</p><div class="related-links">' + links + '</div></div></section>'
