from pathlib import Path
import re, shutil
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist'
RED=ROOT/'redesign'
index=OUT/'index.html'
doc=index.read_text()
home=(RED/'home.html').read_text()
# Preserve the generated global header/footer, metadata, structured data and all existing routes.
doc=re.sub(r'<main id="main">.*?</main>',home,doc,flags=re.S)
doc=doc.replace('<link rel="stylesheet" href="experience.css">','<link rel="stylesheet" href="experience.css"><link rel="stylesheet" href="cinematic.css">')
doc=doc.replace('<script src="experience.js" defer></script>','<script src="experience.js" defer></script><script src="cinematic.js" defer></script>')
# The new homepage is light-first; browser chrome follows the approved visual direction.
doc=doc.replace('<meta name="theme-color" content="#06080D">','<meta name="theme-color" content="#F2F0EA">')
index.write_text(doc)
shutil.copy2(RED/'cinematic.css',OUT/'cinematic.css')
shutil.copy2(RED/'cinematic.js',OUT/'cinematic.js')
print('Applied VisionCraft cinematic homepage redesign.')
