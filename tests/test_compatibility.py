from pathlib import Path
import unittest,tempfile,shutil,json,subprocess,os,base64,sys,importlib.util
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('media_import',ROOT/'scripts/import-media.py');imp=importlib.util.module_from_spec(spec);spec.loader.exec_module(imp)
class Compatibility(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'site';shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('.git','__pycache__','node_modules'));self.env={**os.environ,'SITE_MODE':'preview','FORM_BACKEND':'draft','CMS_GITHUB_REPO':''}
 def tearDown(self):self.tmp.cleanup()
 def build(self,**env):subprocess.run([sys.executable,'scripts/build.py'],cwd=self.root,env={**self.env,**env},check=True,capture_output=True)
 def test_uploaded_image_reaches_home_and_case_without_code_changes(self):
  target=self.root/'dist/images/pavilion.webp';payload={'version':1,'assets':[{'path':'images/uploads/new-work.webp','data':base64.b64encode(target.read_bytes()).decode()}],'items':[]};m=json.loads((self.root/'data/media.json').read_text())['items'][1];m['src']='images/uploads/new-work.webp';m['alt']='Updated carbon platform presentation';payload['items']=[m];p=self.root/'update.json';p.write_text(json.dumps(payload));imp.apply(p,self.root);before=(self.root/'data/media.json').read_bytes();self.build();self.assertEqual(before,(self.root/'data/media.json').read_bytes())
  for page in ['index.html','work.html','work-karbon-kreds.html','web-design.html']:
   s=(self.root/'dist'/page).read_text();self.assertIn('images/uploads/new-work.webp',s);self.assertIn('Updated carbon platform presentation',s)
 def test_image_can_become_video_without_layout_edits(self):
  p=self.root/'data/media.json';data=json.loads(p.read_text());m=data['items'][1];m['src']='images/coffee-process.mp4';m['poster']='images/karbonkreds-website.jpg';p.write_text(json.dumps(data));self.build();s=(self.root/'dist/index.html').read_text();self.assertIn('<video data-media-id="karbonkreds-website.jpg"',s);self.assertIn('preload="none"',s)
 def test_invalid_import_leaves_media_untouched(self):
  before=(self.root/'data/media.json').read_bytes();p=self.root/'update.json';p.write_text(json.dumps({'version':1,'items':[],'assets':[{'path':'../../bad.js','data':'YQ=='}]}))
  with self.assertRaises(ValueError):imp.apply(p,self.root)
  self.assertEqual(before,(self.root/'data/media.json').read_bytes())
 def test_production_and_private_contracts(self):
  self.build(SITE_MODE='production',NETLIFY='true',FORM_BACKEND='netlify',CMS_GITHUB_REPO='owner/repository')
  self.assertIn('data-netlify="true"',(self.root/'dist/contact.html').read_text());self.assertEqual(json.loads((self.root/'dist/admin/config.json').read_text())['backend']['repo'],'owner/repository');self.assertNotIn('thank-you',(self.root/'dist/sitemap.xml').read_text());self.assertNotIn('/admin',(self.root/'dist/sitemap.xml').read_text())
  self.build(FORM_BACKEND='netlify',NETLIFY='false');self.assertNotIn('data-backend="netlify"',(self.root/'dist/contact.html').read_text());self.assertFalse(json.loads((self.root/'dist/admin/connection.json').read_text())['enabled'])
if __name__=='__main__':unittest.main()
