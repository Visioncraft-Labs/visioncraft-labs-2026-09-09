(()=>{
 document.documentElement.classList.add('vc-js');
 const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
 const reveals=[...document.querySelectorAll('.vc-reveal')];
 if(!reduce&&'IntersectionObserver'in window){const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('vc-in');io.unobserve(e.target)}}),{threshold:.14});reveals.forEach(el=>io.observe(el));}else reveals.forEach(el=>el.classList.add('vc-in'));
 const stage=document.querySelector('.vc-hero-stage');
 if(stage&&!reduce&&matchMedia('(pointer:fine)').matches){window.addEventListener('pointermove',e=>{const x=(e.clientX/innerWidth-.5)*8,y=(e.clientY/innerHeight-.5)*-7;stage.style.transform=`translate3d(${x}px,${y}px,0)`},{passive:true});}
 const cards=[...document.querySelectorAll('.vc-project-card')];
 if(!reduce&&matchMedia('(pointer:fine)').matches)cards.forEach(card=>{card.addEventListener('pointermove',e=>{const r=card.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;card.style.transform=`perspective(900px) rotateY(${x*3}deg) rotateX(${-y*3}deg) translateY(-4px)`});card.addEventListener('pointerleave',()=>card.style.transform='');});
 const dialog=document.getElementById('vc-film-dialog'),video=dialog?.querySelector('video'),close=dialog?.querySelector('.vc-film-close');
 document.querySelectorAll('[data-film]').forEach(btn=>btn.addEventListener('click',()=>{if(!dialog||!video)return;video.src=btn.dataset.film;dialog.showModal();video.play().catch(()=>{});}));
 const closeFilm=()=>{if(!dialog||!video)return;video.pause();video.removeAttribute('src');video.load();dialog.close();};close?.addEventListener('click',closeFilm);dialog?.addEventListener('click',e=>{if(e.target===dialog)closeFilm()});
 document.querySelectorAll('[data-wa]').forEach(a=>{a.href='https://wa.me/16478324443?text='+encodeURIComponent('Hi VisionCraft Labs, I would like to discuss a project.');});
 // The supplied brand logo remains the canonical mark. Canvas adds depth/light only; it never redraws or changes the logo geometry.
 const canvas=document.getElementById('vc-hero-canvas');if(!canvas||reduce)return;
 const ctx=canvas.getContext('2d',{alpha:true});if(!ctx)return;document.documentElement.classList.add('vc-webgl');
 const img=new Image();img.src='images/visioncraft-official-logo.webp';let t=0,raf=0,visible=true;
 const resize=()=>{const d=Math.min(devicePixelRatio||1,1.6),r=canvas.getBoundingClientRect();canvas.width=Math.max(1,r.width*d);canvas.height=Math.max(1,r.height*d);ctx.setTransform(d,0,0,d,0,0)};resize();addEventListener('resize',resize,{passive:true});
 const obs=new IntersectionObserver(es=>{visible=es[0]?.isIntersecting;if(visible&&!raf)draw()});obs.observe(canvas);
 function draw(){raf=0;if(!visible||!img.complete)return;const w=canvas.clientWidth,h=canvas.clientHeight;ctx.clearRect(0,0,w,h);t+=.008;const iw=Math.min(w*.72,680),ih=iw*(img.naturalHeight/img.naturalWidth),x=w*.5-iw*.5+Math.sin(t)*9,y=h*.5-ih*.5+Math.cos(t*.8)*12;ctx.save();ctx.translate(w*.5,h*.5);ctx.rotate(Math.sin(t*.45)*.015);ctx.translate(-w*.5,-h*.5);ctx.shadowColor='rgba(0,0,0,.24)';ctx.shadowBlur=45;ctx.shadowOffsetY=30;ctx.drawImage(img,x,y,iw,ih);ctx.restore();const g=ctx.createRadialGradient(w*.62,h*.38,0,w*.62,h*.38,w*.36);g.addColorStop(0,'rgba(255,174,132,.12)');g.addColorStop(.55,'rgba(101,74,190,.05)');g.addColorStop(1,'rgba(0,0,0,0)');ctx.fillStyle=g;ctx.fillRect(0,0,w,h);raf=requestAnimationFrame(draw)}img.onload=draw;
})();
