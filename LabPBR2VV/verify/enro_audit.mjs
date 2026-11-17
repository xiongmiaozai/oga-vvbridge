#!/usr/bin/env node
/**
 * enro_audit.mjs — 用真实 Chromium 把用户上传的 Java 包跑一遍真实转换，
 * 逐项核对「用户报的贴图」在源包里是否存在、是否被转换、输出到哪里。
 *
 * 前置：chromium --headless=new --no-sandbox --remote-debugging-port=9222 \
 *          --user-data-dir=/tmp/chrome-enro file:///workspace/LabPBR2VV/LabPBR2VV.html
 * 运行：node verify/enro_audit.mjs <java.zip 路径>
 */
import { writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.CDP_PORT || 9222);
const SRC = process.argv[2] || '/tmp/enro/enro.zip';
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function getPageTarget() {
  for (let i = 0; i < 80; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
      const page = list.find(t => t.type === 'page' && t.url.includes('LabPBR2VV.html'));
      if (page) return page;
    } catch (e) { /* 未监听 */ }
    await sleep(250);
  }
  throw new Error('找不到 CDP 页面目标');
}

const target = await getPageTarget();
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = e => rej(new Error('WS 失败')); });

let seq = 0;
const pending = new Map();
ws.onmessage = ev => {
  const msg = JSON.parse(ev.data);
  if (!msg.id || !pending.has(msg.id)) return;
  const { resolve, reject } = pending.get(msg.id);
  pending.delete(msg.id);
  msg.error ? reject(new Error(msg.method + ': ' + JSON.stringify(msg.error))) : resolve(msg.result);
};
const send = (method, params = {}) => new Promise((resolve, reject) => {
  const id = ++seq;
  pending.set(id, { resolve, reject });
  ws.send(JSON.stringify({ id, method, params }));
});
async function evaluate(expression) {
  const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true, timeout: 300000 });
  if (r.exceptionDetails) {
    const d = r.exceptionDetails;
    throw new Error('页面异常: ' + (d.exception?.description || d.text));
  }
  return r.result.value;
}

await send('Runtime.enable');
await send('Page.enable');
await send('DOM.enable');
await send('Page.reload', { ignoreCache: true });
await sleep(1200);

// ---- 1) 通过真实 file input 上传源包（走页面自己的 change 处理器）
const doc = await send('DOM.getDocument', { depth: 1 });
const q = await send('DOM.querySelector', { nodeId: doc.root.nodeId, selector: '#file' });
if (!q.nodeId) throw new Error('找不到 #file');
await send('DOM.setFileInputFiles', { files: [SRC], nodeId: q.nodeId });

// 等扫描完成
let scanned = null;
for (let i = 0; i < 240; i++) {
  scanned = await evaluate(`({ n: (typeof GROUPS!=='undefined'?GROUPS.length:-1),
      src: (typeof DETECTED!=='undefined'&&DETECTED)?DETECTED.name:null,
      fmt: (typeof DETECTED!=='undefined'&&DETECTED)?DETECTED.packFormat:null,
      era: (typeof DETECTED!=='undefined'&&DETECTED&&DETECTED.packFormat!=null)?javaEraOf(DETECTED.packFormat):null })`);
  if (scanned.n > 0) break;
  await sleep(250);
}
if (!scanned || scanned.n <= 0) throw new Error('扫描未完成');
console.log('扫描完成：', JSON.stringify(scanned));

// ---- 2) 逐项核查源包内配对情况（用它自己的 GROUPS）
const audit = await evaluate(`(async function(){
  const want = {
    '末地框架侧面':['end_portal_frame_side'],
    '末地框架顶面':['end_portal_frame_top'],
    '绯红木板':['crimson_planks'],
    '诡异木板':['warped_planks'],
    '盔甲全套':['armor'],
    '地图':['/map/'],
    '耕地干':['farmland'],
    '耕地湿':['farmland_moist'],
    '睡莲':['lily_pad'],
    '玫瑰':['poppy'],
    '牡丹':['peony'],
    '高蕨':['large_fern'],
    '矮蕨':['/fern.png'],
    '向日葵':['sunflower'],
    '丁香':['lilac']
  };
  const out = {};
  for (const [label, kws] of Object.entries(want)) {
    const hits = GROUPS.filter(g => kws.some(k => (g.key||'').includes(k)));
    out[label] = hits.map(g => ({ key:g.key.replace(/^.*textures\\//,''),
      hasS:!!g.spec, hasN:!!g.norm }));
  }
  return { groups: GROUPS.length,
    withSpec: GROUPS.filter(g=>g.spec).length,
    withNorm: GROUPS.filter(g=>g.norm).length,
    audit: out };
})()`);

// ---- 3) 真实转换
const conv = await evaluate(`(async function(){
  await convert();
  const fileCount = (REPORT.output && REPORT.output.files) || 0;
  const st = { converted:REPORT.output.converted, skipped:REPORT.output.skipped,
    noSpecular:REPORT.output.noSpecular, normalMaps:REPORT.output.normalMaps,
    files:fileCount, tgaBase:(REPORT.output.tgaBaseColors||0),
    armorLayers:(REPORT.output.armorLayers||0), skipArmorLayer:(REPORT.output.skippedArmorLayer||0),
    skipNoPBR:(REPORT.output.skippedNonPBRDir||0),
    unmapped:(REPORT.unmappedNames||[]).length };
  const buf = new Uint8Array(await OUT.arrayBuffer());
  let s=''; const CH=0x8000;
  for (let i=0;i<buf.length;i+=CH) s += String.fromCharCode.apply(null, buf.subarray(i,i+CH));
  return { st, b64: btoa(s) };
})()`);

writeFileSync(path.join(HERE, 'out', 'enro_audit.json'),
  JSON.stringify({ scanned, audit, conv: { ...conv, b64: undefined } }, null, 2));
writeFileSync(path.join(HERE, 'out', 'enro_converted.mcpack'), Buffer.from(conv.b64, 'base64'));

ws.close();
