"""Apply a Media Studio export to a local checkout; never publishes."""
from pathlib import Path
import sys,json,base64,re,hashlib,shutil,tempfile
from media import MediaCollection
ROOT=Path(__file__).resolve().parents[1]
def apply(path,root=ROOT):
 path=Path(path)
 if path.stat().st_size>200_000_000:raise ValueError('Update package is too large')
 data=json.loads(path.read_text());original=json.loads((root/'data/media.json').read_text());known={m['id']:m for m in original['items']}
 if data.get('version')!=1:raise ValueError('Unsupported update version')
 assets={};updates={}
 for a in data['assets']:
  if not re.fullmatch(r'images/uploads/[a-zA-Z0-9_-]+\.(jpg|jpeg|png|webp|avif|mp4|webm)',a['path']):raise ValueError('Invalid upload path')
  b=base64.b64decode(a['data'],validate=True)
  if not b or len(b)>25_000_000:raise ValueError('Invalid file size')
  if a['path'] in assets:raise ValueError('Duplicate upload')
  dest=root/'dist'/a['path']
  if dest.exists() and dest.read_bytes()!=b:raise ValueError('Refusing to overwrite another upload')
  assets[a['path']]=b
 for m in data['items']:
  if m['id'] not in known or m['id'] in updates:raise ValueError('Unknown or duplicate media placement')
  updates[m['id']]=m
 if not updates:raise ValueError('No saved changes in this package')
 referenced={m.get(k) for m in updates.values() for k in ['src','poster']}
 if set(assets)-referenced:raise ValueError('Unreferenced uploads in package')
 candidate={'items':[updates.get(m['id'],m) for m in original['items']]}
 # Validate the entire change in isolation before touching the source collection.
 with tempfile.TemporaryDirectory() as temp:
  trial=Path(temp);(trial/'data').mkdir();shutil.copytree(root/'dist/images',trial/'dist/images')
  for p,b in assets.items():
   target=trial/'dist'/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
  (trial/'data/media.json').write_text(json.dumps(candidate,indent=2));MediaCollection(trial)
 for p,b in assets.items():
  target=root/'dist'/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
 target=root/'data/media.json';tmp=target.with_suffix('.tmp');tmp.write_text(json.dumps(candidate,indent=2));tmp.replace(target)
 return len(updates)
if __name__=='__main__':
 if len(sys.argv)!=2:raise SystemExit('Usage: python3 scripts/import-media.py path/to/visioncraft-media-update.json')
 print('Applied',apply(sys.argv[1]),'media replacements. Run npm run build and review before publishing.')
