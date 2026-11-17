#!/usr/bin/env node
/**
 * diag_unmapped.mjs — 诊断「特定 Java 贴图未转换成功」
 *
 * 做法：在页面内用 zipStore() 造一个只含待测名字的 Java LabPBR 包（基色 + _s），
 * 走真实 scan()/mapName()/convert() 全链路，再把每组判定与输出名导出。
 * 不修改原型源码。
 *
 * 用法：先起 Chromium（见 run_all.sh 第 2 步），再 node verify/diag_unmapped.mjs
 */
import { readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.CDP_PORT || 9222);
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function getPageTarget() {
  for (let i = 0; i < 60; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
      const page = list.find(t => t.type === 'page' && t.url.includes('LabPBR2VV.html'));
      if (page) return page;
    } catch { /* 尚未监听 */ }
    await sleep(250);
  }
  throw new Error('找不到 CDP 页面目标');
}

const target = await getPageTarget();
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = e => rej(new Error('WS 失败')); });
let seq = 0; const pending = new Map();
ws.onmessage = ev => {
  const m = JSON.parse(ev.data);
  if (!m.id || !pending.has(m.id)) return;
  const { resolve, reject } = pending.get(m.id); pending.delete(m.id);
  m.error ? reject(new Error(JSON.stringify(m.error))) : resolve(m.result);
};
const send = (method, params = {}) => new Promise((resolve, reject) => {
  const id = ++seq; pending.set(id, { resolve, reject });
  ws.send(JSON.stringify({ id, method, params }));
});
async function evaluate(expression, awaitPromise = true) {
  const r = await send('Runtime.evaluate', { expression, awaitPromise, returnByValue: true, userGesture: true });
  if (r.exceptionDetails) throw new Error('页面异常: ' + JSON.stringify(r.exceptionDetails).slice(0, 600));
  return r.result.value;
}

await send('Runtime.enable');
const env = await evaluate(`(function(){ return { ready: typeof convert==='function' && typeof zipStore==='function' && typeof scan==='function' }; })()`);
if (!env.ready) throw new Error('页面未就绪');

// 待测的 Java 侧名称（全部按 Java 真实路径放置）
const CASES = [
  ['末地传送门（方块本体）', 'assets/minecraft/textures/block/end_portal.png'],
  ['末地传送门框架 侧面', 'assets/minecraft/textures/block/end_portal_frame_side.png'],
  ['末地传送门框架 顶面', 'assets/minecraft/textures/block/end_portal_frame_top.png'],
  ['末地传送门框架 眼睛', 'assets/minecraft/textures/block/end_portal_frame_eye.png'],
  ['绯红木板', 'assets/minecraft/textures/block/crimson_planks.png'],
  ['诡异木板', 'assets/minecraft/textures/block/warped_planks.png'],
  ['盔甲 钻石 层1', 'assets/minecraft/textures/models/armor/diamond_layer_1.png'],
  ['盔甲 钻石 层2', 'assets/minecraft/textures/models/armor/diamond_layer_2.png'],
  ['盔甲 铁 层1', 'assets/minecraft/textures/models/armor/iron_layer_1.png'],
  ['地图背景', 'assets/minecraft/textures/map/map_background.png'],
  ['地图图标', 'assets/minecraft/textures/map/map_icons.png'],
  ['耕地（干）', 'assets/minecraft/textures/block/farmland.png'],
  ['耕地（湿）', 'assets/minecraft/textures/block/farmland_moist.png'],
  ['睡莲', 'assets/minecraft/textures/block/lily_pad.png'],
  ['玫瑰/虞美人', 'assets/minecraft/textures/block/poppy.png'],
  ['玫瑰（旧名）', 'assets/minecraft/textures/block/rose.png'],
  ['牡丹 上', 'assets/minecraft/textures/block/peony_top.png'],
  ['牡丹 下', 'assets/minecraft/textures/block/peony_bottom.png'],
  ['高蕨 上', 'assets/minecraft/textures/block/large_fern_top.png'],
  ['高蕨 下', 'assets/minecraft/textures/block/large_fern_bottom.png'],
  ['矮蕨', 'assets/minecraft/textures/block/fern.png'],
  ['向日葵 前', 'assets/minecraft/textures/block/sunflower_front.png'],
  ['向日葵 顶', 'assets/minecraft/textures/block/sunflower_top.png'],
  ['丁香 上', 'assets/minecraft/textures/block/lilac_top.png'],
  ['丁香 下', 'assets/minecraft/textures/block/lilac_bottom.png'],
];

const out = await evaluate(`(async function(){
  const CASES = ${JSON.stringify(CASES)};
  const mk = (c) => makePNG(8, 8, () => c);
  const E = [{ name:'pack.mcmeta', data: enc({ pack:{ pack_format:15, description:'diag' } }) }];
  for (const [, p] of CASES){
    const e = p.replace(/\\.png$/, '_s.png');
    E.push({ name: p, data: await mk(p.endsWith('/fern.png') ? [120,140,160,100] : [120,140,160,255]) });
    E.push({ name: e, data: await mk([200,240,90,0]) });
  }
  const ab = await zipStore(E).arrayBuffer();
  ZIP = await openZip(ab);
  GROUPS = scan(ZIP);

  const rows = [];
  for (const [, p] of CASES){
    const key = p.replace(/\\.png$/, '');
    const g = GROUPS.find(x => x.key === key);
    if (!g) { rows.push({ java:p, status:'未扫描到' }); continue; }
    const m = mapName(g.color || g.spec || '', {});
    rows.push({ java:p, src:m.src, dir:m.dir, out:'textures/' + m.dir + '/' + m.name + '.png', changed:m.changed });
  }

  // 真实转换，收集输出文件名（OUT 是 zip Blob，重新打开读清单）
  await convert();
  const oz = await openZip(await OUT.arrayBuffer());
  const files = oz.names.slice();
  const buf = new Uint8Array(await OUT.arrayBuffer());
  let bin = '';
  for (let i=0;i<buf.length;i++) bin += String.fromCharCode(buf[i]);
  return { rows, files, b64: btoa(bin), report: REPORT };
})()`);

// node 侧与官方基岩清单比对
let bedrock = new Set();
try {
  for (const f of ['/tmp/bedrock_blocks.txt', '/tmp/bedrock_armor.txt']) {
    const txt = readFileSync(f, 'utf8');
    for (const l of txt.split('\n')) if (l.trim()) bedrock.add(l.trim().replace(/\.[^.]+$/, ''));
  }
} catch { /* 无清单则跳过比对 */ }

console.log('\n=== 逐项诊断（Java 名 → 转换器输出 → 基岩是否存在）===');
const lines = [];
for (const r of out.rows) {
  const base = (r.out || '').split('/').pop().replace(/\.png$/, '');
  const stem = (r.out || '').replace(/\.png$/, '');
  const inPack = (out.files || []).includes(stem + '.png') || (out.files || []).includes(stem + '.tga');
  const inB = bedrock.size ? bedrock.has(base) : null;
  const verdict = !r.out ? '扫描不到'
    : (inB === false ? '基岩无此名 → 无效'
      : (inB === true ? '名称对得上' : '未比对'));
  const line = [r.java.padEnd(46), (r.src || '').padEnd(8), (r.out || '').padEnd(52), inPack ? '已入包' : '未入包', inB === null ? '' : (inB ? '基岩有' : '基岩无'), verdict].join(' ');
  console.log(line);
  lines.push({ ...r, inPack, bedrockHas: inB, verdict });
}

writeFileSync(path.join(HERE, 'out', 'diag_unmapped.json'), JSON.stringify(lines, null, 2));
writeFileSync(path.join(HERE, 'out', 'diag_output_files.json'), JSON.stringify(out.files, null, 2));
if (out.b64) writeFileSync(path.join(HERE, 'out', 'diag_pack.mcpack'), Buffer.from(out.b64, 'base64'));
console.log('\n输出文件总数:', (out.files || []).length);
ws.close();
