#!/usr/bin/env node
/**
 * gen_final.mjs — 用更新后的转换器对真包跑完整转换并通过浏览器下载产物。
 * 前置：chromium --headless=new --no-sandbox --remote-debugging-port=9222 \
 *          --user-data-dir=/tmp/chrome-bedtest file:///workspace/LabPBR2VV/LabPBR2VV.html
 * 运行：node verify/gen_final.mjs /tmp/enro/enro.zip <输出路径>
 */
import fs from 'node:fs';
import path from 'node:path';
const PORT=9222, SRC=process.argv[2]||'/tmp/enro/enro.zip';
const DLNAME=process.argv[3]||'ENRO_0.20.2_主体_128x_转换版.mcpack';
const DLROOT='/workspace/_dl';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
fs.mkdirSync(DLROOT,{recursive:true});
// 清理下载目录
for(const f of fs.readdirSync(DLROOT)) fs.rmSync(path.join(DLROOT,f),{force:true});

const l=await(await fetch(`http://127.0.0.1:${PORT}/json`)).json();
const t=l.find(x=>x.type==='page'&&x.url.includes('LabPBR2VV.html'));
if(!t)throw new Error('找不到页面目标');
const ws=new WebSocket(t.webSocketDebuggerUrl);
await new Promise((res,rej)=>{ws.onopen=res;ws.onerror=e=>rej(new Error('WS'));});
let seq=0;const pend=new Map();
ws.onmessage=ev=>{const m=JSON.parse(ev.data);if(!m.id||!pend.has(m.id))return;const{resolve,reject}=pend.get(m.id);pend.delete(m.id);m.error?reject(new Error(JSON.stringify(m.error))):resolve(m.result);};
const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++seq;pend.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
const ev=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true,timeout:300000});if(r.exceptionDetails)throw new Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result.value;};

await send('Runtime.enable');await send('Page.enable');await send('DOM.enable');
// 设置下载行为(新CDP API)
const browser=await(await fetch(`http://127.0.0.1:${PORT}/json/version`)).json();
await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:DLROOT,eventsEnabled:true}).catch(()=>{});
await send('Page.reload',{ignoreCache:true});await sleep(1200);
for(let i=0;i<80;i++){let ok=false;try{ok=await ev("typeof convert==='function'&&typeof reuvBed==='function'");}catch(e){}if(ok)break;await sleep(250);}
// 上传真包
const doc=await send('DOM.getDocument',{depth:1});
const q=await send('DOM.querySelector',{nodeId:doc.root.nodeId,selector:'#file'});
await send('DOM.setFileInputFiles',{files:[SRC],nodeId:q.nodeId});
for(let i=0;i<240;i++){const n=await ev("typeof GROUPS!=='undefined'?GROUPS.length:-1");if(n>0)break;await sleep(250);}
// 复原旧版选项 + 开启床重排
await ev(`(function(){
  document.querySelector('#metal').value='binary';
  document.querySelector('#optSss').checked=true;
  document.querySelector('#optNormal').checked=false;
  document.querySelector('#optFlip').checked=false;
  document.querySelector('#optFallback').checked=true;
  document.querySelector('#optStack').checked=false;
  document.querySelector('#optI18n').checked=true;
  document.querySelector('#optBed').checked=true;
  document.querySelector('#engine').value='1,21,120';
  document.querySelector('#packname').value='ENRO 0.20.2 主体 128x（VV转换版）';
  return 'set';
})()`);
console.log('开始转换…');
await ev('convert()');
for(let i=0;i<400;i++){const b=await ev("BUSY");if(!b)break;await sleep(250);}
const rep=await ev("({bedUV:REPORT.bedUV,output:REPORT.output})");
console.log('报告:',JSON.stringify(rep));
// 触发下载
await ev('download(OUT,'+JSON.stringify(DLNAME)+')');
// 等待下载完成
let file=null;
for(let i=0;i<240;i++){
  const files=fs.readdirSync(DLROOT).filter(f=>!f.endsWith('.crdownload'));
  if(files.length){file=path.join(DLROOT,files[0]);break;}
  await sleep(500);
}
if(!file)throw new Error('下载未完成');
const size=fs.statSync(file).size;
console.log('下载完成:',file,size,'bytes');
ws.close();
