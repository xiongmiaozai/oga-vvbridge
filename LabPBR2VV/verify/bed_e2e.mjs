#!/usr/bin/env node
/**
 * bed_e2e.mjs — 端到端验证床 UV 重排集成是否正确。
 * 前置：chromium --headless=new --no-sandbox --remote-debugging-port=9222 \
 *          --user-data-dir=/tmp/chrome-bedtest file:///workspace/LabPBR2VV/LabPBR2VV.html
 * 运行：node verify/bed_e2e.mjs /tmp/enro/enro.zip
 * 输出：verify/out/bed_e2e_black.rgba / report.json ，供 Python 逐像素核对
 */
import { writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const HERE = path.dirname(fileURLToPath(import.meta.url));
const OUTDIR = path.resolve(HERE,'out');
const PORT = Number(process.env.CDP_PORT || 9222);
const SRC = process.argv[2] || '/tmp/enro/enro.zip';
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function getPageTarget(){
  for (let i=0;i<80;i++){
    try{ const l=await(await fetch(`http://127.0.0.1:${PORT}/json`)).json();
      const p=l.find(t=>t.type==='page'&&t.url.includes('LabPBR2VV.html')); if(p)return p; }catch(e){}
    await sleep(250);
  }
  throw new Error('找不到 CDP 页面目标');
}
const target=await getPageTarget();
const ws=new WebSocket(target.webSocketDebuggerUrl);
await new Promise((res,rej)=>{ws.onopen=res;ws.onerror=e=>rej(new Error('WS 失败'));});
let seq=0; const pending=new Map();
ws.onmessage=ev=>{const m=JSON.parse(ev.data);if(!m.id||!pending.has(m.id))return;
  const{resolve,reject}=pending.get(m.id);pending.delete(m.id);
  m.error?reject(new Error(m.method+': '+JSON.stringify(m.error))):resolve(m.result);};
const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
async function evaluate(expression){
  const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true,timeout:300000});
  if(r.exceptionDetails){const d=r.exceptionDetails;throw new Error('页面异常: '+(d.exception?.description||d.text));}
  return r.result.value;
}
await send('Runtime.enable');await send('Page.enable');await send('DOM.enable');
await send('Page.reload',{ignoreCache:true});await sleep(1000);
for(let i=0;i<80;i++){
  let ok=false;try{ok=await evaluate("typeof convert==='function'&&typeof loadAB==='function'&&typeof reuvBed==='function'");}catch(e){}
  if(ok)break;await sleep(250);
}
// 上传真包
const doc=await send('DOM.getDocument',{depth:1});
const q=await send('DOM.querySelector',{nodeId:doc.root.nodeId,selector:'#file'});
await send('DOM.setFileInputFiles',{files:[SRC],nodeId:q.nodeId});
let n=-1;
for(let i=0;i<240;i++){n=await evaluate("typeof GROUPS!=='undefined'?GROUPS.length:-1");if(n>0)break;await sleep(250);}
console.log('扫描到组数:',n);
// 确保 optBed 勾选
await evaluate("document.querySelector('#optBed').checked=true; document.querySelector('#optNormal').checked=false; 'ok'");
// 直接调 convert()
await evaluate("convert()");
for(let i=0;i<240;i++){const b=await evaluate("BUSY");if(!b)break;await sleep(250);}
// 读取报告统计 + 反解输出包里的床图
const res=await evaluate(`(async function(){
  const rep = REPORT ? {bedUV:REPORT.bedUV, output:REPORT.output} : null;
  const out = OUT; if(!out) return {rep, err:'no OUT'};
  const zip = await unzipNative(await out.arrayBuffer());
  const names = zip.names.filter(n=>/entity\\/bed\\/(black|red|white)\\.png$/.test(n));
  const imgs = {};
  for(const nm of names){
    const im = await decodePNG(new Uint8Array(await zip.get(nm)));
    imgs[nm] = {w:im.w,h:im.h,data:Array.from(im.data)};
  }
  return {rep, imgs};
})()`);
if(res.err) throw new Error(res.err);
writeFileSync(path.join(OUTDIR,'bed_e2e_report.json'),JSON.stringify(res.rep,null,2));
for(const [nm,im] of Object.entries(res.imgs)){
  const safe=nm.replace(/[^a-z0-9]+/gi,'_');
  writeFileSync(path.join(OUTDIR,'bed_e2e_'+safe+'.raw'),Buffer.from(im.data));
  console.log('提取',nm,im.w+'x'+im.h,im.data.length+'bytes');
}
console.log('报告:',JSON.stringify(res.rep?.bedUV));
ws.close();
