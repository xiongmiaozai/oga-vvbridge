#!/usr/bin/env node
// 提取端到端输出包里 black 床的 MERS TGA 与 _s 源，供 Python 核对重排同步性
import { writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const HERE=path.dirname(fileURLToPath(import.meta.url)), OUTDIR=path.resolve(HERE,'out');
const PORT=9222, sleep=ms=>new Promise(r=>setTimeout(r,ms));
const l=await(await fetch(`http://127.0.0.1:${PORT}/json`)).json();
const t=l.find(x=>x.type==='page'&&x.url.includes('LabPBR2VV.html'));
const ws=new WebSocket(t.webSocketDebuggerUrl);
await new Promise((res,rej)=>{ws.onopen=res;ws.onerror=rej;});
let seq=0;const pend=new Map();
ws.onmessage=ev=>{const m=JSON.parse(ev.data);if(!m.id||!pend.has(m.id))return;const{resolve,reject}=pend.get(m.id);pend.delete(m.id);m.error?reject(new Error(JSON.stringify(m.error))):resolve(m.result);};
const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++seq;pend.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
const ev=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true,timeout:300000});if(r.exceptionDetails)throw new Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result.value;};
const r=await ev(`(async function(){
  const zip=await unzipNative(await OUT.arrayBuffer());
  const mers=new Uint8Array(await zip.get('textures/entity/bed/black_mers.tga'));
  const nrm=await zip.get('textures/entity/bed/black_normal.tga');
  return {mers:mers?Array.from(mers):null, normal:nrm?Array.from(new Uint8Array(nrm)):null,
    hasNormal:!!nrm};
})()`);
if(r.mers)writeFileSync(path.join(OUTDIR,'bed_e2e_black_mers.tga'),Buffer.from(r.mers));
if(r.normal)writeFileSync(path.join(OUTDIR,'bed_e2e_black_normal.tga'),Buffer.from(r.normal));
console.log('MERS bytes',r.mers?.length,'normal bytes',r.normal?.length,'hasNormal',r.hasNormal);
ws.close();
