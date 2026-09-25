(()=>{'use strict';
const login=document.getElementById('login'),hq=document.getElementById('hq');
const showHQ=()=>{login.classList.add('hidden');hq.classList.remove('hidden')};
const lockHQ=()=>{sessionStorage.removeItem('vc-hq-preview');hq.classList.add('hidden');login.classList.remove('hidden')};
document.getElementById('signin').onclick=()=>{sessionStorage.setItem('vc-hq-preview','1');showHQ()};
document.getElementById('logout').onclick=lockHQ;
if(sessionStorage.getItem('vc-hq-preview')==='1')showHQ();
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));t.classList.add('active')});
const ids=['destLocal','destGoogle','destIcloud'],boxes=ids.map(id=>document.getElementById(id)).filter(Boolean),mode=document.getElementById('backupMode'),save=document.getElementById('saveDest');
const labels={destLocal:'Local / NAS',destGoogle:'Google Drive',destIcloud:'iCloud'};
const key='vc-hq-backup-destinations-v1';
function selected(){return boxes.filter(x=>x.checked).map(x=>x.id)}
function render(){if(!mode)return;const names=selected().map(id=>labels[id]);mode.textContent='Mode: '+(names.length?names.join(' + '):'No backup destination selected');mode.className=names.length?'ok':''}
try{const stored=JSON.parse(localStorage.getItem(key)||'null');if(Array.isArray(stored))boxes.forEach(x=>x.checked=stored.includes(x.id))}catch(_){}
boxes.forEach(x=>x.onchange=render);
if(save)save.onclick=()=>{const values=selected();localStorage.setItem(key,JSON.stringify(values));render();save.textContent='Saved on this device';setTimeout(()=>save.textContent='Save Selection',1600)};
render();
})();