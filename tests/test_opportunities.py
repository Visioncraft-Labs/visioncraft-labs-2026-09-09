from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import opportunities

NOW = datetime(2026, 10, 5, 8, tzinfo=timezone.utc)


def project(ident=42, title='Etsy listing image design', **values):
    return {'id': ident, 'title': title, 'status': 'active', 'description': 'Create Etsy listing images and a clear shop brand.',
            'time_submitted': NOW.timestamp(), 'jobs': [], **values}


class Opportunities(unittest.TestCase):
    def test_filters_private_closed_stale_and_unrelated_projects(self):
        items = [project(), project(43, nonpublic=True), project(44, status='closed'),
                 project(45, time_submitted=(NOW-timedelta(days=8)).timestamp()),
                 project(46, title='Football stats', description='Research sports data')]
        self.assertEqual([x['id'] for x in opportunities.select_projects({'Etsy': items}, NOW)], [42])

    def test_deduplicates_and_prioritizes_etsy_without_trusting_remote_urls(self):
        item = project(title='Etsy shop web design', url='javascript:alert(1)')
        data = opportunities.select_projects({'web design': [item, project(43, title='Web design', description='Web design work')], 'Etsy': [item]}, NOW)
        self.assertEqual(data[0]['id'], 42)
        self.assertEqual(set(data[0]['matches']), {'Etsy', 'web design'})
        self.assertEqual(data[0]['url'], 'https://www.freelancer.com/projects/42')
        self.assertEqual(len(data), 2)

    def test_partial_source_failure_preserves_last_good_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'opportunities.json'; target.write_text('{"previous":true}')
            def fetch(query):
                if query == 'branding': raise OSError('Unavailable')
                return [project()]
            with self.assertRaises(OSError): opportunities.refresh(target, fetch, NOW)
            self.assertEqual(target.read_text(), '{"previous":true}')

    def test_valid_empty_refresh_replaces_previous_projects(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'opportunities.json'; target.write_text('{"previous":true}')
            result = opportunities.refresh(target, lambda query: [], NOW)
            self.assertEqual(result['projects'], [])
            self.assertEqual(json.loads(target.read_text())['queries'], list(opportunities.QUERIES))

    def test_dashboard_escapes_untrusted_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / 'data').mkdir()
            payload={'checked_at': NOW.isoformat(), 'projects': [{'id':42,'title':'<script>alert(1)</script>', 'summary':'<img src=x onerror=alert(1)>', 'matches':['Etsy'], 'posted_at':NOW.isoformat()}]}
            (root / 'data/opportunities.json').write_text(json.dumps(payload))
            (root / 'dist').mkdir(); opportunities.build_dashboard(root)
            page=(root / 'dist/admin/opportunities.html').read_text()
            self.assertNotIn('<script>alert(1)', page); self.assertNotIn('<img src=x', page)
            self.assertIn('&lt;script&gt;', page)
            self.assertIn('noindex,nofollow', page)


if __name__ == '__main__': unittest.main()
