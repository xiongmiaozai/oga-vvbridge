#!/usr/bin/env node
/**
 * cdp_run.mjs — 在真实 Chromium 里驱动 M0 原型跑完整转换流程
 *
 * 前置：chromium --headless=new --no-sandbox --remote-debugging-port=9222 \
 *          --user-data-dir=/tmp/chrome-pbr2vv file:///workspace/LabPBR2VV/LabPBR2VV.html
 * 运行：node verify/cdp_run.mjs
 *
 * 产出：
 *   /workspace/LabPBR2VV/示例_LabPBR2VV.mcpack   可直接导入基岩版的样例包
 *   verify/out/report.json                      原型内生成的 _pbr2vv_report.json
 *   verify/out/cdp_result.json                  本脚本的断言与产物摘要
 *
 * 说明：本脚本不修改原型源码，只通过 CDP 调用页面已有的全局函数，
 *       因此验证的是「用户实际打开页面后会发生什么」。
 */
import { writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const PORT = Number(process.env.CDP_PORT || 9222);

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function getPageTarget() {
  for (let i = 0; i < 60; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
      const page = list.find(t => t.type === 'page' && t.url.includes('LabPBR2VV.html'));
      if (page) return page;
    } catch (e) { /* Chromium 尚未监听 */ }
    await sleep(250);
  }
  throw new Error('找不到 CDP 页面目标；请确认 Chromium 已带 --remote-debugging-port 启动');
}

const target = await getPageTarget();
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  ws.onopen = resolve;
  ws.onerror = e => reject(new Error('WebSocket 连接失败: ' + (e.message || e)));
});

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
  const r = await send('Runtime.evaluate', {
    expression, awaitPromise: true, returnByValue: true, timeout: 180000
  });
  if (r.exceptionDetails) {
    const d = r.exceptionDetails;
    throw new Error('页面异常: ' + (d.exception?.description || d.text));
  }
  return r.result.value;
}

await send('Runtime.enable');
await send('Page.enable');
// 每次验证强制重载，确保测的是磁盘上最新源码，而不是 Chromium 缓存的旧页面
await send('Page.reload', { ignoreCache: true });
await sleep(300);

// 等待页面脚本执行完毕（顶层 const/function 进入全局词法环境）
let ready = false;
for (let i = 0; i < 60; i++) {
  try {
    ready = await evaluate("typeof convert === 'function' && typeof buildDemo === 'function' && typeof BUILTIN_MAP === 'object' && typeof encodePNGBytes === 'function'");
  } catch (e) { ready = false; }   // reload 期间执行上下文会重建
  if (ready) break;
  await sleep(250);
}
if (!ready) throw new Error('原型脚本未在页面中就绪');

/* ---------- 1) 环境探针 ---------- */
const env = await evaluate(`(function(){
  let ds = false; try { new DecompressionStream('deflate-raw'); ds = true; } catch(e){}
  let canvas = false; try { canvas = !!document.createElement('canvas').getContext('2d'); } catch(e){}
  return { userAgent: navigator.userAgent, deflateRaw: ds, canvas2d: canvas,
           builtinTableSize: BUILTIN_MAP_SIZE, actualTableSize: Object.keys(BUILTIN_MAP).length,
           zipIndicator: document.querySelector('#zipmode').textContent };
})()`);

/* ---------- 2) 映射表抽样断言（证明内置表在页面里生效） ---------- */
const mapChecks = await evaluate(`(function(){
  const cases = [
    ['assets/minecraft/textures/block/black_wool.png', {}, 'wool_colored_black', 'builtin'],
    ['assets/minecraft/textures/block/grass_block_side.png', {}, 'grass_side', 'builtin'],
    ['assets/minecraft/textures/block/iron_block.png', {}, 'iron_block', 'none'],
    ['assets/minecraft/textures/block/iron_block.png', {iron_block:'my_iron'}, 'my_iron', 'custom'],
    ['assets/minecraft/textures/item/apple.png', {}, 'apple', 'none']
  ];
  return cases.map(function(c){
    const m = mapName(c[0], c[1]);
    return { input:c[0], dir:m.dir, got:m.name, want:c[2], src:m.src, wantSrc:c[3],
             pass: m.name===c[2] && m.src===c[3] };
  });
})()`);

/* ---------- 3) 通道算法回归断言（在真实浏览器引擎里跑） ---------- */
const algoChecks = await evaluate(`(function(){
  const opt = { metal:'binary', sss:true };
  const cases = [
    ['s=255 完全光滑 -> rough=0',      labpbrToMers(255,0,0,255,opt), [0,0,0,0]],
    ['s=0 完全粗糙 -> rough=255',      labpbrToMers(0,0,0,0,opt),     [0,0,255,0]],
    ['s=128 -> rough=63(精确值)',      labpbrToMers(128,0,0,0,opt),   [0,0,63,0]],
    ['g=229 介电质 -> metal=0',        labpbrToMers(255,229,0,255,opt),[0,0,0,0]],
    ['g=230 金属 -> metal=255',        labpbrToMers(255,230,0,255,opt),[255,0,0,0]],
    ['a=255 保留值 -> emis=0',         labpbrToMers(255,0,0,255,opt), [0,0,0,0]],
    ['a=254 -> emis=255',              labpbrToMers(255,0,0,254,opt), [0,255,0,0]],
    ['b=64 孔隙率丢弃 -> sss=0',       labpbrToMers(255,0,64,255,opt),[0,0,0,0]],
    ['b=255 最大 SSS -> sss=255',      labpbrToMers(255,0,255,255,opt),[0,0,0,255]],
    ['金属与 SSS 互斥(金属胜)',        labpbrToMers(255,230,130,255,opt),[255,0,0,0]],
    ['SSS 胜则金属清零',               labpbrToMers(255,0,255,255,opt),[0,0,0,255]],
    ['平面法线 Z 重建',                splitNormal(128,128,0,0,false), [128,128,255]],
    ['平面法线 flipY 不改变 X/Z',      splitNormal(128,128,0,0,true),  [128,127,255]],
    ['X=255 时 Z 归零',                splitNormal(255,128,0,0,false), [255,128,128]]
  ];
  return cases.map(function(c){
    return { name:c[0], got:c[1], want:c[2], pass: c[1].every(function(v,i){ return v===c[2][i]; }) };
  });
})()`);

/* ---------- 3.4) alpha 非预乘保真断言：alpha=0 的 _s 像素 RGB 不能被抹成 0 ---------- */
const alphaChecks = await evaluate(`(async function(){
  const src = new Uint8Array([
    210,231,20,0,     // 金属 _s：高平滑/F0/SSS，alpha=0（无自发光）
    30,20,30,0,       // 石头 _s：alpha=0
    90,40,200,254,    // 发光 _s：alpha=254
    128,128,255,140   // 法线 _n：alpha=140
  ]);
  const pngBlob = await encodePNGBytes(4,1,src); // 非预乘编码 → Blob
  const png = new Uint8Array(await pngBlob.arrayBuffer());
  const dec = await decodePNG(png);              // 非预乘解码
  const c = [];
  const eq = (a,b) => a.length===b.length && a.every(function(v,i){return v===b[i];});
  c.push({ name:'PNG 4x1 解码尺寸正确', got:[dec.w,dec.h], want:[4,1], pass:dec.w===4&&dec.h===1 });
  c.push({ name:'alpha=0 像素① RGB 原样保留（非预乘）', got:Array.from(dec.data.slice(0,4)), want:[210,231,20,0], pass:eq(Array.from(dec.data.slice(0,4)),[210,231,20,0]) });
  c.push({ name:'alpha=0 像素② RGB 原样保留（非预乘）', got:Array.from(dec.data.slice(4,8)), want:[30,20,30,0], pass:eq(Array.from(dec.data.slice(4,8)),[30,20,30,0]) });
  c.push({ name:'alpha=254 像素原样保留', got:Array.from(dec.data.slice(8,12)), want:[90,40,200,254], pass:eq(Array.from(dec.data.slice(8,12)),[90,40,200,254]) });
  const m = labpbrToMers(dec.data[0],dec.data[1],dec.data[2],dec.data[3],{metal:'binary',sss:true});
  c.push({ name:'alpha=0 仍算出正确粗糙度（若被预乘会变255）', got:m[2], want:'0<rough<100', pass:m[2]>0&&m[2]<100 });
  return c;
})()`);

/* ---------- 3.5) 包名自动识别断言（pack.mcmeta / 文件名兜底 / 清洗） ---------- */
const nameChecks = await evaluate(`(async function(){
  const cases = [];
  cases.push({ name:'清洗 § 颜色码', got: cleanPackName('§6ENRO §7v0.20'), want:'ENRO v0.20' });
  cases.push({ name:'清洗控制字符与多余空白', got: cleanPackName('  a\\u0001  b  '), want:'a b' });
  const z1 = await openZip(await buildDemo());
  const r1 = await detectPackName(z1, 'ignored.zip');
  cases.push({ name:'pack.mcmeta 优先', got: r1 && r1.name + '|' + r1.source,
               want:'PBR2VV 演示包|pack.mcmeta' });
  const z2 = await openZip(await zipStore([{ name:'textures/blocks/x.png', data: enc('x') }]).arrayBuffer());
  const r2 = await detectPackName(z2, 'ENRO 0.20网易版2.mcpack');
  cases.push({ name:'无 mcmeta 走文件名兜底', got: r2 && r2.name + '|' + r2.source,
               want:'ENRO 0.20网易版2|文件名' });
  return cases.map(function(c){ return { name:c.name, got:c.got, want:c.want, pass: c.got===c.want }; });
})()`);

/* ---------- 3.6) 典型 Java LabPBR 包：贴图扫描 + 名称/目录识别 ---------- */
const javaChecks = await evaluate(`(async function(){
  const cases = [];
  const z = await openZip(await zipStore([
    { name:'pack.mcmeta', data: enc({ pack:{ pack_format:15, description:'§6ENRO §7v0.20\\nby me' } }) },
    { name:'assets/minecraft/textures/block/iron_block.png',   data: enc('a') },
    { name:'assets/minecraft/textures/block/iron_block_s.png', data: enc('b') },
    { name:'assets/minecraft/textures/block/iron_block_n.png', data: enc('c') },
    { name:'assets/minecraft/textures/block/polished_andesite.png', data: enc('d') },
    { name:'assets/minecraft/textures/item/apple.png',          data: enc('e') },
    { name:'assets/mypack/textures/block/custom_thing.png',     data: enc('f') }
  ]).arrayBuffer());
  const gs = scan(z);
  const iron = gs.find(g => g.key.endsWith('iron_block'));
  cases.push({ name:'_s/_n 自动配对成一组', got: !!(iron && iron.color && iron.spec && iron.norm), want:true });
  cases.push({ name:'共识别 4 组贴图', got: gs.length, want:4 });
  const m1 = mapName('assets/minecraft/textures/block/polished_andesite.png', {});
  cases.push({ name:'Java 名映射 polished_andesite', got: m1.name+'|'+m1.src, want:'stone_andesite_smooth|builtin' });
  const m2 = mapName('assets/minecraft/textures/item/apple.png', {});
  cases.push({ name:'item/ 自动分到 items', got: m2.dir, want:'items' });
  const m3 = mapName('assets/mypack/textures/block/custom_thing.png', {});
  cases.push({ name:'自定义命名空间仍归 blocks', got: m3.dir+'|'+m3.src, want:'blocks|none' });
  const pn = await detectPackName(z, 'whatever.zip');
  cases.push({ name:'§ 描述自动识别为包名', got: pn && pn.name, want:'ENRO v0.20' });
  return cases.map(function(c){ return { name:c.name, got:c.got, want:c.want, pass: c.got===c.want }; });
})()`);

/* ---------- 3.7) 封面：输出侧统一生成合规的基岩 pack_icon.png ---------- */
const iconProbe = await evaluate(`(async function(){
  window.requestAnimationFrame = function(cb){ return setTimeout(function(){ cb(0); }, 0); };
  const cover = await makePNG(64,64,function(x,y){ return [x*4%256, y*4%256, (x+y)*2%256, 255]; });
  const color = await makePNG(4,4,function(){ return [10,20,30,255]; });
  const spec  = await makePNG(4,4,function(){ return [100,0,0,0]; });
  const base = [
    { name:'pack.mcmeta', data: enc({ pack:{ pack_format:15, description:'封面测试包' } }) },
    { name:'assets/minecraft/textures/block/iron_block.png',   data: color },
    { name:'assets/minecraft/textures/block/iron_block_s.png', data: spec }
  ];
  async function run(entries, custom){
    CUSTOM_ICON = custom || null;
    const z = await openZip(await zipStore(entries).arrayBuffer());
    ZIP = z; GROUPS = scan(z); DETECTED = null;
    document.querySelector('#packname').value = '封面测试';
    document.querySelector('#metal').value = 'binary';
    document.querySelector('#optSss').checked = true;
    document.querySelector('#optNormal').checked = false;
    document.querySelector('#optFlip').checked = false;
    document.querySelector('#optFallback').checked = false;
    await convert();
    const out = await openZip(await OUT.arrayBuffer());
    const names = out.names.filter(function(n){ return /^pack_icon\\./i.test(n); });
    const got = names.length ? new Uint8Array(await out.get(names[0])) : null;
    const isPNG = !!got && got[0]===0x89 && got[1]===0x50 && got[2]===0x4e && got[3]===0x47;
    const w = isPNG ? ((got[16]<<24)|(got[17]<<16)|(got[18]<<8)|got[19])>>>0 : 0;
    const h = isPNG ? ((got[20]<<24)|(got[21]<<16)|(got[22]<<8)|got[23])>>>0 : 0;
    return { name:names[0]||null, count:names.length, isPNG:isPNG, w:w, h:h,
             bytes: got ? Array.from(got) : null,
             icon: REPORT.icon, failures: REPORT.failures.length };
  }
  const r1 = await run([{ name:'pack.png', data: cover }].concat(base), null);
  const r2 = await run(base, null);
  const custom = await makePNG(32,32,function(){ return [12,34,56,255]; });
  const r3 = await run(base, custom);
  CUSTOM_ICON = null;

  // 源 pack.png 经规整后的期望像素，逐点比对
  const src = await decodePNG(cover);
  const norm = normalizeIcon(src);
  let pxMatch = false, pxDiff = -1;
  if (r1.bytes){
    const dec = await decodePNG(new Uint8Array(r1.bytes));
    pxMatch = dec.w === 128 && dec.h === 128;
    if (pxMatch){
      for (let i=0; i<128*128; i++){
        for (let k=0; k<4; k++) if (dec.data[i*4+k] !== norm[i*4+k]){ pxMatch=false; pxDiff=i; break; }
        if (!pxMatch) break;
      }
    }
  }
  // 自定义封面：32×32 纯色放大到 128×128，应仍是同一纯色
  let customPure = false;
  if (r3.bytes){
    const d3 = await decodePNG(new Uint8Array(r3.bytes));
    customPure = d3.w===128 && d3.h===128 && d3.data[0]===12 && d3.data[1]===34
                 && d3.data[2]===56 && d3.data[3]===255
                 && d3.data[(127*128+127)*4]===12 && d3.data[(127*128+127)*4+2]===56;
  }
  return { r1:{ name:r1.name, count:r1.count, isPNG:r1.isPNG, w:r1.w, h:r1.h,
                 icon:r1.icon, failures:r1.failures, pxMatch:pxMatch, pxDiff:pxDiff },
           r2:{ name:r2.name, count:r2.count, isPNG:r2.isPNG, w:r2.w, h:r2.h, icon:r2.icon },
           r3:{ name:r3.name, count:r3.count, isPNG:r3.isPNG, w:r3.w, h:r3.h,
                icon:r3.icon, customPure:customPure } };
})()`);
const iconChecks = [
  { name:'输出封面固定为 pack_icon.png', got: iconProbe.r1.name, want:'pack_icon.png',
    pass: iconProbe.r1.name === 'pack_icon.png' },
  { name:'包内只有一个封面文件', got: iconProbe.r1.count, want:1,
    pass: iconProbe.r1.count === 1 },
  { name:'封面为 128×128 正方形 2 幂 PNG（CPACKICON）',
    got: iconProbe.r1.w + 'x' + iconProbe.r1.h, want:'128x128',
    pass: iconProbe.r1.isPNG===true && iconProbe.r1.w===128 && iconProbe.r1.h===128 },
  { name:'源 pack.png 规整后像素逐点一致', got: iconProbe.r1.pxMatch, want:true,
    pass: iconProbe.r1.pxMatch === true },
  { name:'报告记录沿用来源 pack.png 与原尺寸 64×64',
    got: iconProbe.r1.icon && iconProbe.r1.icon.source, want:'pack.png',
    pass: !!(iconProbe.r1.icon && iconProbe.r1.icon.source==='pack.png'
             && iconProbe.r1.icon.original.w===64 && iconProbe.r1.icon.original.h===64) },
  { name:'该次转换无失败组', got: iconProbe.r1.failures, want:0,
    pass: iconProbe.r1.failures === 0 },
  { name:'无封面时回退中性占位且合规',
    got: iconProbe.r2.icon && iconProbe.r2.icon.source, want:'placeholder',
    pass: !!(iconProbe.r2.icon && iconProbe.r2.icon.source==='placeholder'
             && iconProbe.r2.name==='pack_icon.png' && iconProbe.r2.isPNG===true
             && iconProbe.r2.w===128 && iconProbe.r2.h===128 && iconProbe.r2.count===1) },
  { name:'自定义封面优先于源包并规整到 128×128',
    got: iconProbe.r3.icon && iconProbe.r3.icon.source, want:'custom',
    pass: !!(iconProbe.r3.icon && iconProbe.r3.icon.source==='custom'
             && iconProbe.r3.w===128 && iconProbe.r3.h===128 && iconProbe.r3.customPure===true) }
];

/* ---------- 3.8) 卫生与叠加：macOS 垃圾过滤 / 非法PNG拦截 / 叠加模式 ---------- */
const hygieneProbe = await evaluate(`(async function(){
  window.requestAnimationFrame = function(cb){ return setTimeout(function(){ cb(0); }, 0); };
  const goodColor = await makePNG(4,4,function(){ return [10,20,30,255]; });
  const goodSpec  = await makePNG(4,4,function(){ return [100,0,0,0]; });
  const entries = [
    { name:'pack.mcmeta', data: enc({ pack:{ pack_format:15, description:'卫生测试' } }) },
    { name:'assets/minecraft/textures/block/iron_block.png',   data: goodColor },
    { name:'assets/minecraft/textures/block/iron_block_s.png', data: goodSpec },
    // macOS AppleDouble 资源叉（内容不是 PNG）
    { name:'assets/minecraft/textures/block/._iron_block.png', data: enc('Mac OS X junk') },
    { name:'__MACOSX/assets/minecraft/textures/block/._foo.png', data: enc('junk') },
    // 文件名含空格（资源位置不合法）
    { name:'assets/minecraft/textures/block/grass side.png', data: goodColor },
    // 名字合法、内容不是 PNG → 应由「基色 PNG 头校验」在输出侧拦下
    { name:'assets/minecraft/textures/block/badpng.png',       data: enc('NOT_A_PNG') },
    { name:'assets/minecraft/textures/block/badpng_s.png',     data: goodSpec },
    // 无 _s 的合法基色 → 触发 noSpec>0，用于验证 pbr/global.json 生成/跳过
    { name:'assets/minecraft/textures/block/plain.png',        data: goodColor }
  ];
  const z = await openZip(await zipStore(entries).arrayBuffer());
  const gs = scan(z);
  const scannedJunk = SCAN_JUNK;
  ZIP = z; GROUPS = gs; DETECTED = null; CUSTOM_ICON = null;
  document.querySelector('#packname').value = '卫生测试';
  document.querySelector('#metal').value = 'binary';
  document.querySelector('#optSss').checked = true;
  document.querySelector('#optNormal').checked = false;
  document.querySelector('#optFlip').checked = false;
  document.querySelector('#optFallback').checked = true;
  document.querySelector('#optStack').checked = false;   // 独立模式
  await convert();
  const out1 = await openZip(await OUT.arrayBuffer());
  const names1 = out1.names.filter(function(n){ return !n.endsWith('/'); });
  const hy1 = REPORT.hygiene;
  const hasGlobal1 = names1.indexOf('pbr/global.json') >= 0;

  // 叠加模式：pbr/global.json 全局单例应被跳过
  document.querySelector('#optStack').checked = true;
  await convert();
  const out2 = await openZip(await OUT.arrayBuffer());
  const names2 = out2.names.filter(function(n){ return !n.endsWith('/'); });
  const hasGlobal2 = names2.indexOf('pbr/global.json') >= 0;
  const stackMode2 = REPORT.options.stackMode;

  let badPng = 0;
  for (const n of names1){
    if (n.toLowerCase().endsWith('.png')){
      const d = new Uint8Array(await out1.get(n));
      if (!(d[0]===0x89 && d[1]===0x50 && d[2]===0x4e && d[3]===0x47)) badPng++;
    }
  }
  const dotJunk = names1.filter(function(n){
    var b = n.split('/').pop(); return b.indexOf('._')===0 || n.indexOf('__MACOSX/')>=0; });
  const spaceName = names1.filter(function(n){ return n.split('/').pop().indexOf(' ')>=0; });
  const seen = {}; const dup = [];
  for (const n of names1){ if (seen[n]) dup.push(n); seen[n] = 1; }
  document.querySelector('#optStack').checked = false;   // 复位，避免污染主流程
  return { scannedJunk: scannedJunk, names1: names1, hy1: hy1,
           hasGlobal1: hasGlobal1, hasGlobal2: hasGlobal2, stackMode2: stackMode2,
           badPng: badPng, dotJunk: dotJunk, spaceName: spaceName, dup: dup,
           ironOk: names1.indexOf('textures/blocks/iron_block_mers.tga') >= 0,
           badpngSkipped: names1.indexOf('textures/blocks/badpng_mers.tga') < 0 };
})()`);
const hygieneChecks = [
  { name:'scan 阶段拦截 3 个 macOS/空格垃圾', got: hygieneProbe.scannedJunk, want:3,
    pass: hygieneProbe.scannedJunk === 3 },
  { name:'输出包无 ._ / __MACOSX 垃圾', got: hygieneProbe.dotJunk.length, want:0,
    pass: hygieneProbe.dotJunk.length === 0 },
  { name:'输出包无空格文件名', got: hygieneProbe.spaceName.length, want:0,
    pass: hygieneProbe.spaceName.length === 0 },
  { name:'输出包无非法 PNG', got: hygieneProbe.badPng, want:0,
    pass: hygieneProbe.badPng === 0 },
  { name:'输出包无重复 ZIP 条目', got: hygieneProbe.dup.length, want:0,
    pass: hygieneProbe.dup.length === 0 },
  { name:'合法组正常转换出 MERS', got: hygieneProbe.ironOk, want:true,
    pass: hygieneProbe.ironOk === true },
  { name:'非法PNG组被整组跳过', got: hygieneProbe.badpngSkipped, want:true,
    pass: hygieneProbe.badpngSkipped === true },
  { name:'报告 hygiene 记录 skip 统计',
    got: hygieneProbe.hy1 && (hygieneProbe.hy1.scanJunkSkipped + '|' + hygieneProbe.hy1.invalidPngSkipped),
    want:'3|1',
    pass: !!(hygieneProbe.hy1 && hygieneProbe.hy1.scanJunkSkipped===3
             && hygieneProbe.hy1.invalidPngSkipped===1) },
  { name:'独立模式生成 pbr/global.json', got: hygieneProbe.hasGlobal1, want:true,
    pass: hygieneProbe.hasGlobal1 === true },
  { name:'叠加模式跳过全局单例 pbr/global.json', got: hygieneProbe.hasGlobal2, want:false,
    pass: hygieneProbe.hasGlobal2 === false },
  { name:'叠加模式写入报告 stackMode', got: hygieneProbe.stackMode2, want:true,
    pass: hygieneProbe.stackMode2 === true }
];

/* ---------- 4) 端到端：生成演示包 → 载入 → 配置 → 转换 → 取回 Blob ---------- */
const EXPR = `(async function(){
  // headless 下 requestAnimationFrame 可能不推进，替换为宏任务，保证 frame() 能 resolve
  window.requestAnimationFrame = function(cb){ return setTimeout(function(){ cb(performance.now()); }, 0); };

  // 用官方包中真实存在的方块名做自定义映射，顺便验证 custom 优先级
  document.querySelector('#mapjson').value = JSON.stringify({
    demo_metal: 'iron_block',
    demo_glow:  'glowstone',
    demo_stone: 'stone',
    demo_plain: 'dirt'
  });
  document.querySelector('#packname').value = 'LabPBR2VV 验证样例';
  document.querySelector('#metal').value = 'binary';
  document.querySelector('#optSss').checked = true;
  document.querySelector('#optNormal').checked = true;   // 打开法线输出
  document.querySelector('#optFlip').checked = false;
  document.querySelector('#optFallback').checked = true; // 打开 pbr/global.json 回退
  document.querySelector('#optStack').checked = false;    // 主流程固定为独立模式

  function toB64(u8){
    let s = '';
    for (let i=0; i<u8.length; i+=0x8000) s += String.fromCharCode.apply(null, u8.subarray(i, i+0x8000));
    return btoa(s);
  }
  const demoAB = await buildDemo();
  const demoB64 = toB64(new Uint8Array(demoAB));
  await loadAB(demoAB, '内置演示包（CDP 自动验证）');
  const packnameAfterLoad = document.querySelector('#packname').value;
  const groups = GROUPS.map(function(g){
    return { key:g.key, color:!!g.color, spec:!!g.spec, norm:!!g.norm,
             mapped: mapName(g.color || g.spec, JSON.parse(document.querySelector('#mapjson').value)).name };
  });
  const scanStats = document.querySelector('#stats').textContent;

  await convert();

  const outAB = await OUT.arrayBuffer();
  const u8 = new Uint8Array(outAB);
  return {
    b64: toB64(u8), demoB64: demoB64, bytes: u8.length, report: REPORT, groups: groups,
    packnameAfterLoad: packnameAfterLoad,
    scanStats: scanStats, summary: document.querySelector('#rsummary').textContent,
    logLines: Array.from(document.querySelectorAll('#log div')).map(function(d){ return d.textContent; })
  };
})()`;

const result = await evaluate(EXPR);

// 端到端里预先手填了包名，自动识别不得覆盖它
nameChecks.push({
  name: '不覆盖用户手动命名', got: result.packnameAfterLoad, want: 'LabPBR2VV 验证样例',
  pass: result.packnameAfterLoad === 'LabPBR2VV 验证样例'
});
// 演示包刻意不带假封面，应走中性占位（不再塞自画的格子图）
iconChecks.push({
  name: '演示包不带假封面 → 中性占位', got: result.report.icon && result.report.icon.source,
  want: 'placeholder', pass: !!(result.report.icon && result.report.icon.source === 'placeholder')
});

/* ---------- 4.9) Java 介绍同步 + 转换记录断言（读主流程产物 OUT/REPORT） ---------- */
const descChecks = await evaluate(`(async function(){
  const rz = await openZip(await OUT.arrayBuffer());
  const mf = JSON.parse(new TextDecoder().decode(new Uint8Array(await rz.get('manifest.json'))));
  const d = mf.header.description || '';
  const c = REPORT.conversion || {};
  const cases = [];
  const has = (s) => d.indexOf(s) >= 0;
  cases.push({ name:'基岩介绍含 Java 原介绍（演示包 pack.mcmeta description）', got:has('PBR2VV 演示包'), want:true, pass:has('PBR2VV 演示包') });
  cases.push({ name:'基岩介绍含转换记录标题', got:has('PBR2VV 转换记录'), want:true, pass:has('PBR2VV 转换记录') });
  cases.push({ name:'基岩介绍含转换时间', got:has('转换时间'), want:true, pass:has('转换时间') });
  cases.push({ name:'基岩介绍含转换工具', got:has('工具：PBR2VV'), want:true, pass:has('工具：PBR2VV') });
  cases.push({ name:'基岩介绍含选项（engine=1.21.120）', got:has('engine=1.21.120'), want:true, pass:has('engine=1.21.120') });
  cases.push({ name:'manifest.description 与 report.conversion.manifestDescription 一致', got:d===c.manifestDescription, want:true, pass:d===c.manifestDescription });
  cases.push({ name:'report.conversion.sourceDescription = 演示包介绍', got:c.sourceDescription, want:'PBR2VV 演示包', pass:c.sourceDescription==='PBR2VV 演示包' });
  cases.push({ name:'report.conversion.sourceDescriptionFromMeta = true', got:c.sourceDescriptionFromMeta, want:true, pass:c.sourceDescriptionFromMeta===true });
  cases.push({ name:'report.conversion.convertedAt 为 ISO 时间', got:c.convertedAt, want:'ISO8601', pass:typeof c.convertedAt==='string' && /^\\d{4}-\\d{2}-\\d{2}T/.test(c.convertedAt) });
  cases.push({ name:'报告记录源包 pack_format=15 与代际 1.15+', got:[c.sourcePackFormat,c.sourceEra].join('/'), want:'15/1.15+', pass:c.sourcePackFormat===15 && c.sourceEra==='1.15+' });
  cases.push({ name:'report.conversion.options 含四类关键选项', got:Object.keys(c.options||{}).length, want:'>=7', pass:['metalPolicy','emitSSS','emitNormal','flipNormalY','emitFallback','stackMode','minEngineVersion'].every(function(k){return k in (c.options||{});}) });
  // 多语言简介模板：包内 texts/ 三件套 + 内容 + 报告记录
  const langJson = rz.get('texts/languages.json') ? JSON.parse(new TextDecoder().decode(new Uint8Array(await rz.get('texts/languages.json')))) : null;
  const zh = await rz.get('texts/zh_CN.lang');
  const en = await rz.get('texts/en_US.lang');
  const zhTxt = zh ? new TextDecoder().decode(new Uint8Array(zh)) : '';
  const enTxt = en ? new TextDecoder().decode(new Uint8Array(en)) : '';
  cases.push({ name:'输出 texts/languages.json 且声明 zh_CN/en_US', got:langJson, want:'zh_CN,en_US', pass:!!langJson && langJson.indexOf('zh_CN')>=0 && langJson.indexOf('en_US')>=0 });
  cases.push({ name:'输出 zh_CN.lang 与 en_US.lang', got:[!!zh,!!en], want:[true,true], pass:!!zh && !!en });
  cases.push({ name:'.lang 含 pack.name / pack.description 覆盖键', got:zhTxt.indexOf('pack.name=')>=0 && zhTxt.indexOf('pack.description=')>=0, want:true, pass:zhTxt.indexOf('pack.name=')>=0 && zhTxt.indexOf('pack.description=')>=0 });
  const NL = String.fromCharCode(10); // 换行，避开模板字符串里的反斜杠转义
  const noBareBreak = zhTxt.split(NL).length <= 4 && zhTxt.indexOf('pack.description=') >= 0;
  cases.push({ name:'.lang 简介换行转义为字面 \\n（无裸换行）', got:noBareBreak, want:true, pass:noBareBreak });
  cases.push({ name:'.lang 保留 Java 原介绍 PBR2VV 演示包', got:zhTxt.indexOf('PBR2VV 演示包')>=0, want:true, pass:zhTxt.indexOf('PBR2VV 演示包')>=0 });
  const loc = REPORT.localization || {};
  cases.push({ name:'报告 localization 记录 languages/files', got:loc.languages, want:'zh_CN,en_US', pass:!!(loc.enabled===true && (loc.files||[]).length===3 && loc.languages.indexOf('zh_CN')>=0 && loc.languages.indexOf('en_US')>=0) });
  cases.push({ name:'报告 conversion.options.localizedDescription = true', got:c.options && c.options.localizedDescription, want:true, pass:!!(c.options && c.options.localizedDescription===true) });
  const multi = cleanDescription('§6第一行\\n§7第二行\\n\\n第三行');
  cases.push({ name:'多行介绍保留换行且去 § 颜色码', got:multi, want:'第一行\\n第二行\\n\\n第三行', pass:multi==='第一行\\n第二行\\n\\n第三行' });
  return cases;
})()`);

/* ---------- 4.10) 材质通道可视化预览断言（调用页面预渲染，检查 canvas 真出图） ---------- */
const previewChecks = await evaluate(`(async function(){
  const cases = [];
  let idx = GROUPS.findIndex(function(g){ return g.color && g.spec; });
  if (idx < 0) idx = GROUPS.findIndex(function(g){ return !!g.color; });
  const hasSpec = !!(GROUPS[idx] && GROUPS[idx].spec);
  await previewGroup(idx);
  await new Promise(function(r){ setTimeout(r, 250); });
  const box = document.querySelector('#preview');
  const canvases = document.querySelectorAll('#pv-imgs canvas');
  cases.push({ name:'点击预览后预览区可见', got:box.hidden, want:false, pass:box.hidden===false });
  cases.push({ name:'有 _s 组生成 6 张通道图（原图+_s+4 通道）', got:canvases.length, want:hasSpec?6:'>=1', pass:hasSpec ? canvases.length===6 : canvases.length>=1 });
  if (hasSpec && canvases.length>=6){
    const c = canvases[5]; // 最后一张 = A 次表面通道
    const px = c.getContext('2d').getImageData(0,0,1,1).data;
    cases.push({ name:'MERS 通道画布像素已写入（alpha=255）', got:[px[0],px[1],px[2],px[3]], want:'a=255', pass:px[3]===255 });
    const st = document.querySelector('#pv-stats').textContent;
    cases.push({ name:'统计栏含金属 / 粗糙度 / SSS', got:st.slice(0,50), want:'含关键词', pass:st.indexOf('金属')>=0 && st.indexOf('粗糙度')>=0 && st.indexOf('SSS')>=0 });
  }
  return cases;
})()`);

/* ---------- 5) 落盘 ---------- */
const mcpack = Buffer.from(result.b64, 'base64');
const demoZip = Buffer.from(result.demoB64, 'base64');
const packPath = path.join(ROOT, '示例_LabPBR2VV.mcpack');
writeFileSync(packPath, mcpack);
writeFileSync(path.join(HERE, 'out', 'input_demo.zip'), demoZip);
writeFileSync(path.join(HERE, 'out', 'report.json'), JSON.stringify(result.report, null, 2));

const summary = {
  generatedAt: new Date().toISOString(),
  env,
  map: { total: mapChecks.length, passed: mapChecks.filter(c => c.pass).length, cases: mapChecks },
  algo: { total: algoChecks.length, passed: algoChecks.filter(c => c.pass).length, cases: algoChecks },
  alpha: { total: alphaChecks.length, passed: alphaChecks.filter(c => c.pass).length, cases: alphaChecks },
  desc: { total: descChecks.length, passed: descChecks.filter(c => c.pass).length, cases: descChecks },
  preview: { total: previewChecks.length, passed: previewChecks.filter(c => c.pass).length, cases: previewChecks },
  name: { total: nameChecks.length, passed: nameChecks.filter(c => c.pass).length, cases: nameChecks },
  java: { total: javaChecks.length, passed: javaChecks.filter(c => c.pass).length, cases: javaChecks },
  icon: { total: iconChecks.length, passed: iconChecks.filter(c => c.pass).length, cases: iconChecks },
  hygiene: { total: hygieneChecks.length, passed: hygieneChecks.filter(c => c.pass).length, cases: hygieneChecks },
  pipeline: {
    packPath, bytes: result.bytes, groups: result.groups, scanStats: result.scanStats,
    summary: result.summary, logLines: result.logLines
  }
};
writeFileSync(path.join(HERE, 'out', 'cdp_result.json'), JSON.stringify(summary, null, 2));

console.log(JSON.stringify({
  env: summary.env,
  map: `${summary.map.passed}/${summary.map.total}`,
  algo: `${summary.algo.passed}/${summary.algo.total}`,
  alpha: `${summary.alpha.passed}/${summary.alpha.total}`,
  desc: `${summary.desc.passed}/${summary.desc.total}`,
  preview: `${summary.preview.passed}/${summary.preview.total}`,
  name: `${summary.name.passed}/${summary.name.total}`,
  java: `${summary.java.passed}/${summary.java.total}`,
  icon: `${summary.icon.passed}/${summary.icon.total}`,
  hygiene: `${summary.hygiene.passed}/${summary.hygiene.total}`,
  packPath, bytes: result.bytes,
  report: result.report.output,
  mapping: result.report.mapping,
  summary: result.summary
}, null, 2));

const failed = summary.map.passed !== summary.map.total
  || summary.algo.passed !== summary.algo.total
  || summary.alpha.passed !== summary.alpha.total
  || summary.desc.passed !== summary.desc.total
  || summary.preview.passed !== summary.preview.total
  || summary.name.passed !== summary.name.total
  || summary.java.passed !== summary.java.total
  || summary.icon.passed !== summary.icon.total
  || summary.hygiene.passed !== summary.hygiene.total;
ws.close();
process.exit(failed ? 1 : 0);
