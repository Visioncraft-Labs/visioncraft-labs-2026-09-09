"""Shared, validated media contract for the frontend and editing tools."""
from pathlib import Path
import json,re,html
class MediaCollection:
 def __init__(self,root):
  self.root=Path(root);self.items={}
  for m in json.loads((self.root/'data/media.json').read_text())['items']:
   if m['id'] in self.items:raise ValueError('Duplicate media ID: '+m['id'])
   self.validate(m);self.items[m['id']]=m
 def is_video(self,src):return Path(src).suffix.lower() in ['.mp4','.webm']
 def validate(self,m):
  for key in ['src','poster']:
   src=m.get(key,'')
   if not src and key=='poster':continue
   if not re.fullmatch(r'images/[A-Za-z0-9_./-]+',src) or '..' in Path(src).parts:raise ValueError('Invalid media path: '+src)
   if not (self.root/'dist'/src).is_file():raise ValueError('Missing media file: '+src)
   if Path(src).suffix.lower() not in ['.jpg','.jpeg','.png','.webp','.avif','.mp4','.webm']:raise ValueError('Unsupported media type')
  if not m.get('alt','').strip():raise ValueError('A media description is required: '+m['id'])
  if m.get('fit') not in ['cover','contain']:raise ValueError('Invalid image fit')
  if not all(isinstance(m.get(k),int) and 1<=m[k]<=16000 for k in ['width','height']):raise ValueError('Invalid media dimensions')
  if self.is_video(m['src']) and (not m.get('poster') or self.is_video(m['poster'])):raise ValueError('Videos need an image poster: '+m['id'])
 def render(self,key,lazy=True,cls=''):
  m=self.items[key];e=html.escape;style=f'object-fit:{m["fit"]};aspect-ratio:{m["width"]}/{m["height"]}'
  attrs=f'data-media-id="{e(key)}" class="{e(cls)}" width="{m["width"]}" height="{m["height"]}" style="{style}"'
  if self.is_video(m['src']):
   mime='video/webm' if m['src'].endswith('.webm') else 'video/mp4'
   return f'<video {attrs} muted loop playsinline controls preload="none" poster="{e(m["poster"])}" aria-label="{e(m["alt"])}"><source src="{e(m["src"])}" type="{mime}"></video>'
  return f'<img {attrs} src="{e(m["src"])}" alt="{e(m["alt"])}" loading="{"lazy" if lazy else "eager"}" decoding="async">'
 def replace_legacy(self,s):
  def replace(m):
   tag=m.group(0)
   if 'data-media-id=' in tag:return tag
   src=re.search(r'src="images/([^"]+)"',tag)
   if src and src[1] in self.items:return self.render(src[1])
   return tag
  s=re.sub(r'<video\b.*?</video>',replace,s,flags=re.S)
  s=re.sub(r'<img\b[^>]*>',replace,s)
  def caption(m):
   block=m.group(0);key=re.search(r'data-media-id="([^"]+)"',block)
   if key and key[1] in self.items:
    value=html.escape(self.items[key[1]].get('caption',''))
    block=re.sub(r'<figcaption>.*?</figcaption>',lambda _: '<figcaption>'+value+'</figcaption>' if value else '',block,flags=re.S)
   return block
  return re.sub(r'<figure\b.*?</figure>',caption,s,flags=re.S)
