'use strict';
(() => {
 let revision=null;
 const bar=document.createElement('div');bar.className='live-update';bar.hidden=true;
 const label=document.createElement('span');label.textContent='New results are available.';
 const refresh=document.createElement('button');refresh.type='button';refresh.textContent='Refresh workspace';refresh.addEventListener('click',()=>location.reload());
 bar.append(label,refresh);document.body.append(bar);
 let editing=false;document.addEventListener('input',e=>{if(e.target.closest('form'))editing=true;});
 async function poll(){
  if(document.hidden)return;
  try{
   const r=await fetch('/workspace/state/',{headers:{'Accept':'application/json'}});if(!r.ok)return;
   const data=await r.json();
   if(revision!==null && data.revision!==revision){
    if(!editing&&!document.querySelector('dialog[open]'))location.reload();else bar.hidden=false;
   }
   revision=data.revision;
  }catch(_){}
 }
 poll();setInterval(poll,10000);
})();