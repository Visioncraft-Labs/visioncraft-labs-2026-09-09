from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,re,subprocess
root=Path(__file__).resolve().parents[1]/'dist'; errors=[]; titles=[]
class Inspect(HTMLParser):
 def __init__(self):super().__init__();self.refs=[];self.ids=set();self.h1=0
 def handle_starttag(self,t,attrs):
  a=dict(attrs)
  if t=='img' and 'alt' not in a:errors.append('Image is missing an explicit alt attribute: '+a.get('src','dynamic image'))
  if t=='img' and a.get('data-media-id') and not a.get('alt','').strip():errors.append('Content image is missing a description: '+a.get('src',''))
  if t=='video':
   if not a.get('aria-label','').strip():errors.append('Video is missing an accessible name: '+a.get('data-media-id','unknown video'))
   if not a.get('aria-describedby','').strip():errors.append('Video is missing a linked text description: '+a.get('data-media-id','unknown video'))
   elif a['aria-describedby']:self.refs.append('#'+a['aria-describedby'])
  if t=='h1':self.h1+=1
  if 'id' in a:self.ids.add(a['id'])
  for key in ['href','src','poster']:
   if key in a:self.refs.append(a[key])
parsed={}
for p in root.rglob('*.html'):
 obj=Inspect();obj.feed(p.read_text());parsed[str(p.relative_to(root))]=obj
 for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>',p.read_text(),re.S):json.loads(raw)
 title=re.search(r'<title>(.*?)</title>',p.read_text()).group(1);titles.append(title)
 public_page=p.relative_to(root).parts[0]!='admin'
 if public_page and obj.h1!=1:errors.append(f'{p.name}: expected one H1, got {obj.h1}')
 if public_page and 'href="#"' in p.read_text():errors.append(f'{p.name}: empty link')
 if re.search(r'\[Next|Reserved slot|Placeholder article|Sample structure',p.read_text()):errors.append(f'{p.name}: unfinished content')
for name,obj in parsed.items():
 for ref in obj.refs:
  u=urlsplit(ref)
  if u.scheme or u.netloc:continue
  path=unquote(u.path);target=(root/path.lstrip('/')) if path.startswith('/') else (root/name).parent/path if path else root/name
  target=target.resolve()
  if not target.exists():errors.append(f'{name}: missing {ref}');continue
  if u.fragment and str(target.relative_to(root)) in parsed and u.fragment not in parsed[str(target.relative_to(root))].ids:errors.append(f'{name}: missing anchor {ref}')
if len(titles)!=len(set(titles)):errors.append('Duplicate titles')
r=subprocess.run(['node','--check',str(root/'experience.js')],capture_output=True,text=True)
if r.returncode:errors.append(r.stderr)
print(f'Checked {len(parsed)} pages, local links, anchors, H1s, structured data and JavaScript.')
if errors:print('\n'.join(errors));raise SystemExit(1)
print('PASS')
