"""Public project discovery; applications remain on the original marketplace."""
import json
import re
from datetime import datetime, timezone, timedelta
from html import escape
from pathlib import Path
from urllib.parse import urlencode
import urllib.request
from refresh_trends import atomic_write, NoRedirects

ROOT = Path(__file__).resolve().parents[1]
QUERIES = ('Etsy', 'web design', 'branding', 'Blender', 'UI UX', 'AI automation', 'product photography', 'video editing')
API = 'https://www.freelancer.com/api/projects/0.1/projects/active/'


def fetch_projects(query):
    url = API + '?' + urlencode({'query': query, 'limit': 30, 'full_description': 'true', 'job_details': 'true'})
    req = urllib.request.Request(url, headers={'User-Agent': 'VisionCraftLabsOpportunityMonitor/1.0', 'Accept': 'application/json'})
    with urllib.request.build_opener(NoRedirects()).open(req, timeout=20) as response:
        payload = response.read(2_000_001)
    if len(payload) > 2_000_000:
        raise ValueError('Project response exceeds size limit')
    result = json.loads(payload)
    if result.get('status') != 'success' or not isinstance(result.get('result', {}).get('projects'), list):
        raise ValueError('Invalid marketplace response')
    return result['result']['projects']


def select_projects(groups, now=None):
    now = now or datetime.now(timezone.utc)
    selected = {}
    for query, projects in groups.items():
        if query not in QUERIES or not isinstance(projects, list):
            raise ValueError('Unsupported project query')
        for project in projects:
            if not isinstance(project, dict):
                raise ValueError('Invalid project record')
            if project.get('status') != 'active' or project.get('deleted') or project.get('nonpublic'):
                continue
            ident = project.get('id')
            if type(ident) is not int or ident <= 0:
                continue
            title = project.get('title', '')
            description = project.get('description') or project.get('preview_description') or ''
            if not isinstance(title, str) or not isinstance(description, str):
                continue
            if not title.strip() or len(title) > 300:
                continue
            posted = project.get('time_submitted') or project.get('submitdate')
            if type(posted) not in (int, float):
                continue
            try:
                date = datetime.fromtimestamp(posted, timezone.utc)
            except (ValueError, OverflowError, OSError):
                continue
            if not now - timedelta(days=7) <= date <= now + timedelta(minutes=10):
                continue
            skills = [job.get('name', '') for job in project.get('jobs', []) if isinstance(job, dict)]
            haystack = ' '.join([title, description, *[s for s in skills if isinstance(s, str)]]).casefold()
            # The API can return loosely related results. Require the requested phrase.
            words = re.findall(r'\w+', query.casefold())
            if not all(re.search(r'\b' + re.escape(word) + r'\b', haystack) for word in words):
                continue
            if ident in selected:
                if query not in selected[ident]['matches']:
                    selected[ident]['matches'].append(query)
                continue
            selected[ident] = {
                'id': ident, 'title': title.strip(), 'summary': ' '.join(description.split())[:280],
                'posted_at': date.isoformat().replace('+00:00', 'Z'),
                'url': 'https://www.freelancer.com/projects/' + str(ident),
                'source': 'Freelancer', 'matches': [query],
            }
    return sorted(selected.values(), key=lambda item: ('Etsy' not in item['matches'], -datetime.fromisoformat(item['posted_at'].replace('Z', '+00:00')).timestamp()))[:100]


def refresh(output=None, fetcher=fetch_projects, now=None):
    now = now or datetime.now(timezone.utc)
    # Fetch all sources before replacement, preserving last-good data on failure.
    groups = {query: fetcher(query) for query in QUERIES}
    projects = select_projects(groups, now)
    snapshot = {'version': 1, 'checked_at': now.isoformat().replace('+00:00', 'Z'),
                'source': API, 'queries': list(QUERIES), 'projects': projects}
    atomic_write(output or ROOT / 'data/opportunities.json', snapshot)
    return snapshot


def build_dashboard(root):
    snapshot = json.loads((root / 'data/opportunities.json').read_text())
    out = root / 'dist/admin'
    cards = ''
    for item in snapshot['projects']:
        # Rebuild the URL from a validated integer, never from fetched markup.
        if type(item.get('id')) is not int or item['id'] <= 0:
            raise ValueError('Invalid stored project ID')
        cards += '<article class="card"><span class="tag">' + escape(' · '.join(item['matches'])) + '</span><h2>' + escape(item['title']) + '</h2><p>' + escape(item['summary']) + '</p><p class="meta">Posted ' + escape(item['posted_at'][:10]) + ' · Freelancer</p><a href="https://www.freelancer.com/projects/' + str(item['id']) + '" target="_blank" rel="noopener noreferrer">Review project ↗</a></article>'
    platforms = [
        ('Freelancer — Etsy briefs', 'https://www.freelancer.com/jobs/etsy/', 'Public project requests included in this daily snapshot.'),
        ('Upwork', 'https://www.upwork.com/nx/search/jobs/?q=etsy', 'Use saved searches and your account’s job alerts.'),
        ('PeoplePerHour', 'https://www.peopleperhour.com/freelance-jobs', 'Search Etsy, branding, web design and video editing.'),
        ('Contra', 'https://contra.com/opportunities', 'Browse design, development and creative opportunities.'),
        ('Fiverr', 'https://www.fiverr.com/', 'Publish defined services and check account-matched briefs.'),
        ('99designs', 'https://99designs.com/contests', 'Review suitable brand and graphic design briefs.'),
        ('Behance', 'https://www.behance.net/joblist', 'Browse creative jobs and freelance work.'),
        ('Dribbble', 'https://dribbble.com/jobs', 'Explore design opportunities.'),
        ('LinkedIn', 'https://www.linkedin.com/jobs/', 'Save searches for contract design, development and creative roles.'),
        ('Etsy', 'https://www.etsy.com/your/shops/me/dashboard', 'Manage your own shop listings and buyer messages; an Etsy shop is required.'),
    ]
    links = ''.join('<article class="card"><h2><a href="' + escape(url) + '" target="_blank" rel="noopener noreferrer">' + escape(label) + ' ↗</a></h2><p>' + escape(note) + '</p></article>' for label, url, note in platforms)
    html = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Project Opportunities | VisionCraft Labs</title><link rel="stylesheet" href="opportunities.css"></head><body><main><a class="back" href="/">← VisionCraft Labs</a><header><span class="eyebrow">VISIONCRAFT LABS · PROJECT DISCOVERY</span><h1>Your next project starts here.</h1><p>Recent public freelance briefs, with Etsy requests first. Review suitability and availability on the original platform before applying.</p></header><p class="meta">Last successful check: ''' + escape(snapshot['checked_at']) + ''' · Daily snapshot · Public listings only</p><label for="filter">Filter project briefs</label><input id="filter" type="search" placeholder="Etsy, Blender, web design…"><p id="count" role="status"></p><section id="projects" class="grid">''' + cards + '''</section><h2 class="section-title">Your marketplace routine</h2><p>These platforms need your account for saved alerts, client messages or applications. Their private inboxes are not connected to this dashboard.</p><section class="grid">''' + links + '''</section><p class="meta">This dashboard is excluded from search indexing. It contains public opportunity data and has no login restriction. Website inquiries arrive separately through the contact page.</p></main><script src="opportunities.js" defer></script></body></html>'''
    out.mkdir(exist_ok=True)
    (out / 'opportunities.html').write_text(html)
    (out / 'opportunities.css').write_text('''*{box-sizing:border-box}body{margin:0;background:#080d15;color:#edf2f8;font:16px/1.65 system-ui,sans-serif}main{max-width:1200px;margin:auto;padding:40px 28px 80px}a{color:#6be1ff;text-decoration:none}a:hover{text-decoration:underline}header{max-width:760px;margin:50px 0 28px}h1{font-size:clamp(36px,6vw,64px);line-height:1.05;letter-spacing:-.045em}h2{font-size:22px;line-height:1.3}.eyebrow,.tag{color:#6be1ff;font-size:12px;letter-spacing:.1em}.meta{color:#a9b6c7;font-size:13px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}.card{padding:24px;border:1px solid #263548;border-radius:18px;background:#101b2b;overflow-wrap:anywhere}.card p{color:#b6c4d5}.section-title{margin-top:64px}input{display:block;width:min(100%,520px);padding:14px;margin:8px 0 20px;border:1px solid #415775;border-radius:10px;background:#101b2b;color:#fff;font:inherit}:focus-visible{outline:2px solid #6be1ff;outline-offset:4px}[hidden]{display:none!important}@media(max-width:900px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:600px){main{padding:24px 20px 60px}.grid{grid-template-columns:1fr}}''')
    (out / 'opportunities.js').write_text('''const input=document.querySelector('#filter'),cards=[...document.querySelectorAll('#projects article')],count=document.querySelector('#count');function filter(){const query=input.value.trim().toLowerCase();let visible=0;for(const card of cards){card.hidden=!card.textContent.toLowerCase().includes(query);if(!card.hidden)visible++;}count.textContent=visible+' matching project briefs';}input.addEventListener('input',filter);filter();''')


if __name__ == '__main__':
    result = refresh()
    print(f"Verified {len(QUERIES)} public searches; saved {len(result['projects'])} recent projects at {result['checked_at']}")
