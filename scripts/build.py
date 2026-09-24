from pathlib import Path
import re,json,html,os

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'dist'; DATA=ROOT/'data'
origin=os.environ.get('SITE_URL','https://visioncraft-labs.com').rstrip('/'); preview=os.environ.get('SITE_MODE','preview')!='production'
E=html.escape
sizes=json.loads((DATA/'media-dimensions.json').read_text())
services=json.loads((DATA/'services.json').read_text()); projects=json.loads((DATA/'projects.json').read_text()); insights=json.loads((DATA/'insights.json').read_text())
original=(ROOT/'templates/home-original.html').read_text(); work=(ROOT/'templates/work-original.html').read_text()
css=re.search(r'<style>(.*?)</style>',original,re.S).group(1)
(OUT/'base.css').write_text(css)
header=re.search(r'<header.*?</header>',original,re.S).group(0)
header=header.replace('<div class="nav-links">','<button class="menu-toggle" aria-expanded="false" aria-controls="primary-menu">Menu</button><div class="nav-links" id="primary-menu">')
footer=re.search(r'<footer>.*?</footer>',original,re.S).group(0)
footer=footer.replace('services.html#websites','web-design.html').replace('services.html#apps','custom-software-development.html').replace('services.html#ai-creative','creative-content.html').replace('services.html#ai-automation','ai-automation.html').replace('services.html#brand','branding.html')
footer=footer.replace('work.html#karbonkreds','work-karbon-kreds.html')
footer=footer.replace('<h4>Company</h4>','<h4>Company</h4><a href="investment.html">Project investment</a>')
from urllib.parse import urlencode
social_links=json.loads((DATA/'socials.json').read_text())
contact=json.loads((DATA/'contact.json').read_text())
def social_anchor(item):
 return f'<a class="social-link social-{E(item["icon"])}" title="{E(item["name"])}" href="{E(item["url"])}" target="_blank" rel="noopener noreferrer" aria-label="VisionCraft Labs on {E(item["name"])} (opens in a new tab)"><img class="social-icon" src="icons/{E(item["icon"])}.svg" width="20" height="20" alt="" aria-hidden="true"></a>'
footer=re.sub(r'<div class="footer-col"><h4>Social</h4>.*?</div>',lambda _: '<div class="footer-col footer-social"><h4>Follow the studio</h4><div class="social-icons">'+''.join(social_anchor(x) for x in social_links)+'</div></div>',footer,flags=re.S)
socials=[x['url'] for x in social_links]
wa='https://wa.me/'+contact['whatsapp']+'?'+urlencode({'text':contact['whatsappMessage']})
def contact_links(doc):
 pattern=r'<a[^>]*href="tel:[^"]+"[^>]*>.*?</a>'
 replacement=f'<span class="contact-channels"><a class="whatsapp-link text-link" href="{E(wa)}" target="_blank" rel="noopener noreferrer" aria-label="Chat on WhatsApp at {E(contact["phoneDisplay"])}"><img class="social-icon whatsapp-icon" src="icons/whatsapp.svg" width="22" height="22" alt="" aria-hidden="true"><span>{E(contact["phoneDisplay"])}</span></a><a class="call-link" href="tel:{E(contact["phone"])}">Call</a></span>'
 return re.sub(pattern,lambda _:replacement,doc,flags=re.S)
meta={}; allpages=[]
from media import MediaCollection
library=MediaCollection(ROOT)
project_media={p['slug']:(p['mediaId'],library.items[p['mediaId']]['alt'],library.items[p['mediaId']]['caption']) for p in projects}
def img(file,alt='',lazy=True,cls=''):
 return library.render(file,lazy=lazy,cls=cls)
def media(p,zoom=True):
 key=p['mediaId'];m=library.items[key];image=img(key)
 return '<figure class="project-media bevel">'+(f'<button class="zoom-media" data-image="{E(m["src"])}" data-caption="{E(m["caption"])}" aria-label="Enlarge {E(p["name"])} project image">{image}<span class="zoom-label">Explore image</span></button>' if zoom and not library.is_video(m['src']) else image)+f'<figcaption>{E(m["caption"])}</figcaption></figure>'
def cta(title='Let’s build what comes next.'):
 return f'<section class="closing"><div class="wrap"><span class="eyebrow">Have an ambitious idea?</span><h2>{title}</h2><div class="hero-ctas"><a class="btn btn-primary" href="contact.html">Start a project</a><a class="btn btn-ghost" href="mailto:visioncraftlabs@gmail.com">Email the studio</a></div></div></section>'
def page(file,title,desc,body,kind='WebPage',extra=None):
 url=origin+('/' if file=='index.html' else '/'+file.removesuffix('.html'))
 schemas=[{'@context':'https://schema.org','@type':'Organization','@id':origin+'/#organization','name':'VisionCraft Labs','url':origin,'logo':origin+'/images/visioncraft-official-logo.webp','sameAs':socials},{'@context':'https://schema.org','@type':kind,'name':title,'description':desc,'url':url,'isPartOf':{'@id':origin+'/#website'}}]
 if file=='index.html':schemas.append({'@context':'https://schema.org','@type':'WebSite','@id':origin+'/#website','url':origin,'name':'VisionCraft Labs'})
 else:schemas.append({'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'Home','item':origin+'/'},{'@type':'ListItem','position':2,'name':title.split(' | ')[0],'item':url}]})
 if extra:schemas.append(extra)
 nav=header.replace(f'href="{file}"',f'href="{file}" aria-current="page"')
 doc=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(title)}</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{url}"><meta name="robots" content="{'noindex,nofollow' if preview or file in ['404.html','thank-you.html'] else 'index,follow'}"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:type" content="{'article' if kind=='Article' else 'website'}"><meta property="og:url" content="{url}"><meta name="twitter:card" content="summary"><meta name="theme-color" content="#06080D"><link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="preconnect" href="https://api.fontshare.com"><link rel="stylesheet" href="base.css"><link rel="stylesheet" href="brand.css"><link rel="stylesheet" href="experience.css"><script type="application/ld+json">{json.dumps(schemas).replace('<','&lt;')}</script><script src="experience.js" defer></script></head><body><a class="skip-link" href="#main">Skip to content</a>{nav}<main id="main">{body}</main>{footer}<dialog id="media-dialog"><form method="dialog"><button class="dialog-close">Close image</button></form><img alt=""><p></p></dialog></body></html>'''
 (OUT/file).write_text(contact_links(doc));allpages.append((file,url));meta[file]=(title,desc)
def hero(label,title,desc):return f'<section class="page-hero"><div class="wrap"><span class="eyebrow">{label}</span><h1>{title}</h1><p>{desc}</p></div></section>'
def project_row(p,i):
 return f'<article class="project-story reveal" id="{p["slug"]}"><div class="project-copy"><span class="project-index">{i:02}</span><span class="eyebrow">{E(p["industry"])}</span><h2><a href="work-{p["slug"]}.html">{E(p["name"])}</a></h2><p>{E(p["summary"])}</p><p class="project-discipline">{E(" · ".join(p["services"]))}</p><a class="text-link" href="work-{p["slug"]}.html">Explore the project</a></div>{media(p)}</article>'
# Homepage: retain the approved two-column introduction and blue/cyan identity; give its right side real work.
def demo():
 return '<div class="automation-demo"><span class="demo-label">VisionCraft Lab · Concept demo</span><div class="demo-incoming"><span>New inquiry: website redesign</span><small>Sample input</small></div><div class="demo-flow"><span class="flow-node">Receive</span><span class="flow-connector"></span><span class="flow-node">Classify</span><span class="flow-connector"></span><span class="flow-node">Draft for review</span></div><p class="demo-output" aria-live="polite">An example of turning a project inquiry into a structured brief.</p><div class="demo-brief"><span>MOCK PROJECT · RETAIL WEBSITE</span><p><b>Intent</b> Website redesign</p><p><b>Route</b> Digital experience team</p><p><b>Next step</b> Review the prepared brief</p></div><div class="demo-controls"><button type="button" data-run-demo>Run example</button><span>Simulated · no message is sent</span></div></div>'
hero_media='<div class="hero-stage"><div class="stage-frame bevel" data-tilt><div class="screen-meta"><span>Selected studio work</span><span id="stage-count">01 / 05</span></div><div class="stage-panels">'
for i,p in enumerate(projects):
 file,alt,cap=project_media[p['slug']]
 tag='div' if library.is_video(library.items[file]['src']) else 'a'
 hero_media+=f'<{tag} class="stage-panel {"active" if i==0 else ""}" href="work-{p["slug"]}.html" data-label="{E(p["name"])} · {E(p["summary"])}" '+('hidden' if i else '')+'>'+img(file,alt,False)+f'</{tag}>'
hero_media+='<div class="stage-panel" data-label="AI Automation · Concept demonstration" hidden>'+demo()+'</div></div><div class="stage-caption" aria-live="polite">Karbon Kreds · Carbon infrastructure &amp; digital platform</div></div><div class="stage-select" aria-label="Choose featured work">'
for i,n in enumerate([p['name'] for p in projects]+['AI Lab']):hero_media+=f'<button class="{"selected" if i==0 else ""}" aria-pressed="{"true" if i==0 else "false"}" data-stage="{i}">{n}</button>'
hero_media+='</div><div class="stage-note">Client work. Studio concepts. Connected capabilities. <button class="rotation-control" data-pause-stage>Pause rotation</button></div></div>'

home=f'''<section class="hero"><div class="wrap"><div class="hero-grid"><div class="hero-copy"><span class="eyebrow">Independent creative technology studio</span><h1>We design brands, build digital products, and create <span class="accent">AI-powered experiences.</span></h1><p class="hero-sub">VisionCraft Labs brings strategy, design and engineering together to turn ambitious ideas into distinctive, commercially focused experiences.</p><div class="hero-ctas"><a class="btn btn-primary" href="#selected">View selected work</a><a class="btn btn-ghost" href="contact.html">Start a project</a></div></div>{hero_media}</div></div></section>
<section class="manifesto"><div class="wrap"><span class="eyebrow">Design. Technology. Intelligence.</span><h2>We don’t decorate businesses.<br><span>We design how they’re experienced.</span></h2><p>From the first impression to the systems behind it. One studio connecting brand, digital experience and business operations.</p></div></section>
<section id="selected" class="selected-work"><div class="wrap"><div class="section-head"><span class="eyebrow">Selected work</span><h2>Proof, in every pixel.</h2></div>{''.join(project_row(p,i+1) for i,p in enumerate(projects))}<a class="text-link" href="work.html">Explore all work and creative production</a></div></section>'''
home+='''<section class="capability-section"><div class="wrap"><div class="section-head"><span class="eyebrow">Connected capabilities</span><h2>One idea.<br>Every dimension.</h2><p>Choose a focused engagement or bring us in from strategy through launch.</p></div><div class="capability-list">'''
for i,s in enumerate(services):home+=f'<a href="{s["slug"]}.html"><span>{i+1:02}</span><h3>{E(s["name"])}</h3><small>{E(s["category"])}</small></a>'
home+='</div></div></section>'
home+=f'''<section class="film-feature"><div class="wrap"><div class="film-copy"><span class="eyebrow">Creative production</span><h2>Make people<br>stop. Look. Feel.</h2><p>Product imagery and short-form films, composed with a clear idea and a precise visual language.</p><a class="text-link" href="work.html#studio-gallery">Explore the visual studio</a></div><div class="film-pair"><figure class="bevel">{img('skincare-jar-orange-glow.jpg','Skincare campaign visual with orange glass art direction')}<figcaption>AI-assisted creative direction</figcaption></figure><figure class="bevel">{img('coffee-process.mp4')}<figcaption>Coffee — bean to cup process</figcaption></figure></div></div></section>'''
home+='<section class="process-section"><div class="wrap"><span class="eyebrow">How we work</span><h2>Business before pixels.</h2><ol class="process-track">'
for title,body in [('Understand','Get close to the business, its audience and the problem worth solving.'),('Define','Agree the direction, the scope and what success needs to mean.'),('Create','Connect identity, content and interface into a coherent experience.'),('Engineer','Build, test and refine for real screens and real use.'),('Evolve','Launch with a maintainable foundation and a clear next step.')]:home+=f'<li class="reveal"><h3>{title}</h3><p>{body}</p></li>'
home+='</ol></div></section>'+cta()
page('index.html','VisionCraft Labs — Branding, Digital Products, Websites & AI','VisionCraft Labs is a creative technology studio building brands, websites, software and AI-powered digital experiences for ambitious companies.',home)
# Work and real project pages.
gallery=re.search(r'<section id="studio-gallery">.*?</section>',work,re.S).group(0)
gallery=gallery.replace('<div class="section-head wide reveal" style="margin-top:80px;">','<div class="section-head wide reveal" id="motion" style="margin-top:80px;">').replace('<video autoplay muted loop playsinline','<video muted loop playsinline controls preload="none"')
gallery=gallery.replace('studio product photography','AI-assisted product composition').replace('studio food photography','creative food composition')
lab='<section><div class="wrap lab-callout"><div><span class="eyebrow">Studio lab · Concept demonstration</span><h2>From an inquiry<br>to a useful first draft.</h2><p>A simulated workflow shows how incoming requests can be classified, routed and prepared for human review. This is a capability demonstration, not a client deployment.</p><a class="text-link" href="ai-automation.html">Explore AI automation</a></div><div class="bevel">'+demo()+'</div></div></section>'
body=hero('Selected work','Ideas transformed<br>into experiences.','Client websites, proprietary software and clearly labelled studio concepts. Explore the thinking as well as the finished work.')
body+='<section class="selected-work"><div class="wrap">'+''.join(project_row(p,i+1) for i,p in enumerate(projects))+'</div></section>'+lab+gallery+cta()
page('work.html','Selected Work & Case Studies | VisionCraft Labs','Explore KarbonKreds website design, Address12 hospitality software, self-initiated campaign concepts and VisionCraft creative production.',body)
for i,p in enumerate(projects):
 body=hero(E(p['industry']),E(p['headline']),E(p['summary']))+f'<section class="case-visual"><div class="wrap">{media(p)}</div></section>'
 body+='<section class="case-story"><div class="wrap"><aside><span class="eyebrow">'+E(p['name'])+'</span><p>'+E(p['status'])+'</p><ul>'+''.join('<li>'+E(x)+'</li>' for x in p['services'])+'</ul></aside><div class="reading">'
 for title,key in [('The challenge','challenge'),('The strategy','strategy'),('Design & engineering','approach'),('The delivery','delivery')]:body+=f'<h2>{title}</h2><p>{E(p[key])}</p>'
 if p['slug']=='karbon-kreds':body+=f'<figure class="bevel">{img("karbon-map.webp","Representative Canadian activity map from the KarbonKreds website")}<figcaption>Representative regional activity map from the live website.</figcaption></figure><a class="btn btn-primary" href="https://karbonkreds.com/" target="_blank" rel="noopener noreferrer">Visit KarbonKreds</a>'
 if p['slug']=='address12':body+='<h2>From booking to back office.</h2><p>Room and rate management support reservations. Guest records connect the stay to billing and communications. Expenses, payroll and reporting bring the operational picture into the same interface.</p><p>Address12 is a local application, so its private operator environment is not linked from this portfolio. Request a demonstration to explore the relevant workflows.</p><a class="btn btn-primary" href="contact.html?project=Address12">Request an Address12 demonstration</a>'
 if p['slug']=='daily-ritual':body+='<h2>From bean to cup</h2>'+img('coffee-process.mp4')+'<p>Illustrative studio motion study, presented as part of this mock campaign.</p>'
 body+='</div></div></section>'
 nextp=projects[(i+1)%len(projects)]; body+=f'<section class="related-band"><div class="wrap"><span class="eyebrow">Continue exploring</span><h2><a href="work-{nextp["slug"]}.html">{nextp["name"]}</a></h2><a class="text-link" href="services.html">Explore our capabilities</a></div></section>'+cta()
 page('work-'+p['slug']+'.html',p['name']+' — '+p['summary']+' | VisionCraft Labs',p['challenge'],body)
# Substantial service content retained from the studio content layer.
body=hero('Capabilities','Strategy to launch.<br>Connected by design.','Branding, websites, digital products, custom software, AI automation and creative production, shaped around the business problem.')+'<section><div class="wrap capability-list">'
for i,s in enumerate(services):body+=f'<a href="{s["slug"]}.html" id="{s["slug"]}"><span>{i+1:02}</span><div><h2>{E(s["name"])}</h2><p>{E(s["description"])}</p></div></a>'
body+='</div></section>'+cta();page('services.html','Branding, Web Design, Software & AI Services | VisionCraft Labs','Explore VisionCraft Labs services for companies in Pakistan and internationally: strategy, identity, websites, custom software, AI and creative production.',body)
service_images={'branding':'skincare-jar-orange-glow.jpg','web-design':'karbonkreds-website.jpg','web-development':'karbonkreds-website.jpg','ui-ux-design':'address12-dashboard.jpg','custom-software-development':'address12-dashboard.jpg','ai-automation':'address12-dashboard.jpg','creative-content':'lipstick-pink-vibes.jpg','product-photography':'candle-oaalses-stone.jpg','seo':'karbon-map.webp'}
for s in services:
 p=next(p for p in projects if p['slug']==s['projects'][0]);body=hero(E(s['name']),E(s['headline']),E(s['description']))
 body+=f'<section class="service-editorial"><div class="wrap"><div class="reading"><span class="eyebrow">The business problem</span><h2>{E(s["name"])} with a clear purpose.</h2><p>{E(s["problem"])}</p></div><figure class="bevel">{img(service_images[s["slug"]],project_media[p["slug"]][1] if service_images[s["slug"]]==project_media[p["slug"]][0] else s["name"]+" — selected studio work")}<figcaption>Selected studio work. {"Address12 uses demonstration data." if service_images[s["slug"]]=="address12-dashboard.jpg" else ""}</figcaption></figure></div></section>'
 body+='<section><div class="wrap reading"><h2>What we can help you build</h2>'
 for c in s['capabilities']:body+=f'<h3>{E(c["title"])}</h3><p>{E(c["body"])}</p>'
 body+='<h2>A clear process</h2><ol>'+''.join('<li>'+E(x)+'</li>' for x in s['process'])+'</ol><h2>Built for everyday use</h2><p>'+E(s['benefit'])+'</p><h3>Tools & handover</h3><p>'+E(s['technology'])+'</p><h2>Questions before you start</h2>'
 for f in s['faqs']:body+=f'<details><summary>{E(f["q"])}</summary><p>{E(f["a"])}</p></details>'
 body+='</div></section>'+(lab if s['slug']=='ai-automation' else '')+'<section class="related-band"><div class="wrap"><span class="eyebrow">Relevant work & thinking</span><div class="related-links">'
 for slug in s['projects']:body+=f'<a href="work-{slug}.html">{next(p["name"] for p in projects if p["slug"]==slug)} case study</a>'
 for slug in s['related']:body+=f'<a href="{slug}.html">{next(x["name"] for x in services if x["slug"]==slug)}</a>'
 body+='<a href="insight-website-redesign-checklist.html">Planning your next website</a></div></div></section>'+cta()
 extra={'@context':'https://schema.org','@type':'Service','name':s['name'],'description':s['description'],'provider':{'@id':origin+'/#organization'}}
 page(s['slug']+'.html',s['name']+' in Pakistan | VisionCraft Labs',s['description'],body,extra=extra)
# Useful complete articles instead of teaser cards with dead links.
body=hero('Studio insights','Better questions.<br>Better digital work.','Practical thinking to help you brief, commission and maintain your next brand or digital project.')+'<section><div class="wrap insight-list">'
for i,a in enumerate(insights):
 image='skincare-jar-orange-glow.jpg' if i==0 else 'karbonkreds-website.jpg'
 body+=f'<article><a href="insight-{a["slug"]}.html" class="bevel">{img(image,a["category"]+" — studio project example")}</a><div><span class="eyebrow">{E(a["category"])}</span><h2><a href="insight-{a["slug"]}.html">{E(a["title"])}</a></h2><p>{E(a["description"])}</p><a class="text-link" href="insight-{a["slug"]}.html">Read the article</a></div></article>'
 article=hero(E(a['category']),E(a['title']),E(a['description']))+'<section><article class="wrap reading"><p class="byline">By VisionCraft Labs · '+E(a['readTime'])+'</p>'
 for sec in a['sections']:article+='<h2>'+E(sec['heading'])+'</h2>'+''.join('<p>'+E(p)+'</p>' for p in sec['paragraphs'])
 article+=f'<p><a class="text-link" href="{a["service"]}.html">Explore {E(next(s["name"] for s in services if s["slug"]==a["service"]))}</a></p></article></section>'+cta()
 page('insight-'+a['slug']+'.html',a['title']+' | VisionCraft Labs',a['description'],article,extra={'@context':'https://schema.org','@type':'Article','headline':a['title'],'author':{'@type':'Organization','name':'VisionCraft Labs'},'publisher':{'@id':origin+'/#organization'},'mainEntityOfPage':origin+'/insight-'+a['slug']})
body+='</div></section>'+cta();page('insights.html','Brand & Website Design Insights | VisionCraft Labs','Practical studio guides on brand identity, website redesign, digital strategy and commissioning better creative and technology work.',body)
# Preserve supplied studio story; replace unsupported filler if present.
for file,title,desc in [('about','Independent Creative Technology Studio | VisionCraft Labs','Meet VisionCraft Labs: an independent studio connecting brand strategy, design, engineering and AI-assisted creative production.'),('privacy','Privacy | VisionCraft Labs','How inquiries and website information are handled by VisionCraft Labs.'),('terms','Website Terms | VisionCraft Labs','Terms for using the VisionCraft Labs website and discussing an engagement.')]:
 s=(ROOT/f'templates/{file}-original.html').read_text();body=re.search(r'<main>(.*?)</main>',s,re.S).group(1);page(file+'.html',title,desc,body)
# Honest inquiry flow: mail draft, never fake delivery on a static private preview.
body=hero('Start a conversation','An ambitious idea<br>starts here.','Tell us what you are building, where things stand and what needs to change. We will use that context to shape the next conversation.')
body+='''<section class="contact-section"><div class="wrap contact-grid"><aside class="contact-info"><span class="eyebrow">Direct to the studio</span><h2>Let’s talk about<br>your next move.</h2><p><a class="text-link" href="mailto:visioncraftlabs@gmail.com">visioncraftlabs@gmail.com</a></p><p><a class="text-link" href="tel:+16478324443">+1 647 832 4443</a></p><p>Prefer to send your own brief? Email your project background, references and timing.</p><div class="social-row">'''+''.join(social_anchor(x) for x in social_links)+'''</div></aside><form id="projectForm" class="inquiry-form"><div class="form-row"><div class="field"><label for="name">Name</label><input required autocomplete="name" id="name" name="name"></div><div class="field"><label for="company">Company</label><input autocomplete="organization" id="company" name="company"></div></div><div class="form-row"><div class="field"><label for="email">Email</label><input required type="email" autocomplete="email" id="email" name="email"></div><div class="field"><label for="phone">Phone / WhatsApp</label><input type="tel" autocomplete="tel" id="phone" name="phone"></div></div><div class="field"><label for="project">Project type</label><select id="project" name="project"><option>Website</option><option>Branding</option><option>Custom software</option><option>Address12 demonstration</option><option>AI / Automation</option><option>Creative content</option><option>SEO / Growth</option><option>Other</option></select></div><div class="form-row"><div class="field"><label for="budget">Estimated budget</label><input id="budget" name="budget" placeholder="Amount and currency, or not sure yet"></div><div class="field"><label for="timeline">Timeline</label><input id="timeline" name="timeline" placeholder="Your preferred launch window"></div></div><div class="field"><label for="description">Project description</label><textarea required id="description" name="description" rows="5"></textarea></div><div class="bot-field" aria-hidden="true"><label for="website">Leave this empty</label><input id="website" name="website" tabindex="-1" autocomplete="off"></div><p class="form-note">This preview prepares an email draft in your mail app. Review it and press Send there to deliver your inquiry.</p><button type="submit" class="btn btn-primary">Prepare project email</button><p id="form-status" role="status"></p><div id="draft-actions" hidden><label for="email-draft">Your prepared brief</label><textarea id="email-draft" rows="8" readonly></textarea><button type="button" class="btn btn-ghost" id="copy-brief">Copy brief</button></div></form></div></section>'''
form_enabled=os.environ.get('FORM_BACKEND','draft')=='netlify' and os.environ.get('NETLIFY')=='true'
if form_enabled:
 body=body.replace('<form id="projectForm" class="inquiry-form">','<form id="projectForm" class="inquiry-form" name="project-inquiry" method="POST" action="/thank-you.html" data-netlify="true" netlify-honeypot="website" data-backend="netlify"><input type="hidden" name="form-name" value="project-inquiry">')
 body=body.replace('This preview prepares an email draft in your mail app. Review it and press Send there to deliver your inquiry.','Your details will be used to respond to this project inquiry.').replace('Prepare project email','Send project inquiry')
page('contact.html' ,'Start a Project | VisionCraft Labs','Discuss a website, branding, custom software, AI automation or creative project with VisionCraft Labs. Send your brief or request an Address12 demonstration.',body)
body=hero('Project investment','A considered scope.<br>A clear investment.','Every engagement starts with the business goal, the work required and the practical constraints. An estimate follows a defined scope.')+'<section><div class="wrap reading"><h2>What shapes an estimate?</h2><p>Strategy, content, design depth, integrations, the number of distinct journeys and the support required after launch all influence the scope. Page count alone is not a useful comparison between proposals.</p><h2>Ways to work together</h2><h3>Focused projects</h3><p>A website, brand identity, software module or creative campaign with agreed deliverables, review points and handover.</p><h3>Custom software & automation</h3><p>Begin with the workflows, permissions, integrations and reliability requirements. Discovery can define a smaller first release before a longer development commitment.</p><h3>Ongoing collaboration</h3><p>SEO, content production, maintenance and product improvement can be scoped as continuing work with clear priorities and review periods.</p><h2>What to share</h2><p>Tell us your intended outcome, current assets and systems, preferred timing and an approximate budget if you have one. “Not sure yet” is a valid starting point.</p><a class="btn btn-primary" href="contact.html">Request a project estimate</a></div></section>'+cta()
page('investment.html','Project Estimates & Investment | VisionCraft Labs','Understand how VisionCraft Labs scopes website, brand, software, AI and creative engagements. Request a project estimate based on your business goals.',body)
page('404.html','Page Not Found | VisionCraft Labs','Find your way back to VisionCraft Labs work, services and contact information.',hero('404','A different direction.','This page could not be found. Our latest work is a good place to continue.')+'<div class="wrap"><a class="btn btn-primary" href="work.html">Explore our work</a></div>'+cta())
page('thank-you.html','Inquiry Received | VisionCraft Labs','Your inquiry has been received.',hero('Thank you','Your next chapter<br>starts here.','Your project inquiry has been received. You can explore our work while we review your brief.')+cta())
# Image dimensions for retained HTML and clearer controls/heading semantics.
for file,_ in allpages:
 p=OUT/file;s=p.read_text();s=re.sub(r'<svg\b[^>]*>\s*<path d="M7 17L17 7M17 7H8M17 7V16"\s*/>\s*</svg>','',s)
 def dims(m):
  tag=m.group(0);src=re.search(r'src="([^"]+)"',tag)
  if src and not re.search(r'\bwidth=',tag):
   f=OUT/src.group(1)
   if f.exists():
    w,h=sizes[f.name];tag=tag.replace('<img',f'<img width="{w}" height="{h}" decoding="async"',1)
  return tag
 s=library.replace_legacy(s);p.write_text(s)
(OUT/'robots.txt').write_text('User-agent: *\nDisallow: /\n' if preview else 'User-agent: *\nAllow: /\nSitemap: '+origin+'/sitemap.xml\n')
(OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+('' if preview else ''.join('<url><loc>'+url+'</loc></url>' for f,url in allpages if f not in ['404.html','thank-you.html']))+'</urlset>')
(OUT/'_headers').write_text('/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n'+('  X-Robots-Tag: noindex, nofollow\n' if preview else ''))
(OUT/'_redirects').write_text('/admin /admin/ 301\n/studio /about 301\n/work/karbon-kreds /work-karbon-kreds 301\n/work/address12 /work-address12 301\n')
print('Built',len(allpages),'pages in', 'private preview' if preview else 'production','mode.')

from admin import build_admin,build_hq
build_admin(ROOT,library,origin,preview)
build_hq(ROOT)

with (OUT/'_headers').open('a') as f:f.write('/admin/*\n  X-Robots-Tag: noindex, nofollow\n  Cache-Control: no-store\n')
