from pathlib import Path
import json,os,re

def build_admin(root,library,origin,preview):
 out=root/'dist/admin';out.mkdir(exist_ok=True)
 repo=os.environ.get('CMS_GITHUB_REPO','');enabled=bool(repo) and not preview
 if repo and not re.fullmatch(r'[\w.-]+/[\w.-]+',repo):raise ValueError('CMS_GITHUB_REPO must be owner/repository')
 fields=[{'name':'id','widget':'hidden'},{'name':'label','label':'Placement name','widget':'string'},{'name':'src','label':'Image or video','widget':'file','choose_url':False},{'name':'poster','label':'Video poster (required for video)','widget':'image','required':False,'choose_url':False},{'name':'alt','label':'Accessible description','widget':'string'},{'name':'caption','label':'Caption','widget':'text','required':False},{'name':'fit','label':'Image fit','widget':'select','options':['contain','cover']},{'name':'width','label':'Presentation width','widget':'number','value_type':'int','min':1,'max':16000},{'name':'height','label':'Presentation height','widget':'number','value_type':'int','min':1,'max':16000}]
 config={'backend':{'name':'github','repo':repo,'branch':os.environ.get('CMS_GITHUB_BRANCH','main')},'publish_mode':'editorial_workflow','media_folder':'dist/images/uploads','public_folder':'images/uploads','site_url':origin,'display_url':origin,'media_library':{'config':{'max_file_size':25000000}},'collections':[{'name':'studio','label':'Studio media','files':[{'name':'media','label':'Images and films','file':'data/media.json','fields':[{'name':'items','label':'Media placements','widget':'list','allow_add':False,'summary':'{{fields.label}}','fields':fields}]}]}]}
 # JSON is valid YAML, consumed by Decap with load_config_file disabled.
 (out/'config.json').write_text(json.dumps(config if enabled else {'enabled':False},indent=2))
 (out/'media.json').write_text(json.dumps({'items':list(library.items.values())},indent=2))
 (out/'connection.json').write_text(json.dumps({'enabled':enabled,'preview':preview}))


def build_hq(root):
 out=root/'dist/admin';out.mkdir(parents=True,exist_ok=True)
 assets=root/'templates/admin'
 for name in ('hq.html','hq.css','hq.js'):
  src=assets/name
  if not src.exists(): raise FileNotFoundError(f'Missing HQ source asset: {src}')
  (out/name).write_text(src.read_text())
