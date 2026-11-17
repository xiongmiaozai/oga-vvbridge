#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_pack.py — 逐文件校验 PBR2VV 产出的 .mcpack，并与输入演示包做逐像素对照

输入：
  ../示例_LabPBR2VV.mcpack      CDP 跑原型导出的成品
  out/input_demo.zip            同一轮 buildDemo() 导出的输入包
  out/report.json               原型内生成的 _pbr2vv_report.json
输出：
  out/pack_check.json           结构化检查结果

校验维度：
  A 包结构      manifest / 目录布局 / 文件数 / 无多余后缀
  B texture_set schema、互斥、值不带扩展名
  C TGA 头（32-bit BGRA 左下原点）与像素逐点比对
  D 输入 PNG 是否被 canvas 预乘 alpha 破坏（演示包规格常量对照）
  E 名称映射、回退 global.json、报告字段自洽
"""
import json
import math
import os
import struct
import zipfile
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
OUT = os.path.join(HERE, 'out')
PACK = os.path.join(ROOT, '示例_LabPBR2VV.mcpack')
DEMO = os.path.join(OUT, 'input_demo.zip')

checks = []


def ck(group, name, ok, detail=''):
    checks.append({'group': group, 'name': name, 'ok': bool(ok), 'detail': str(detail)})
    return bool(ok)


def js_round(v):
    """模拟 JS Math.round（Python round 是银行家舍入，0.5 会归 0）"""
    return int(math.floor(v + 0.5))


# ---------------------------------------------------------------- PNG 解码
def decode_png(data):
    assert data[:8] == b'\x89PNG\r\n\x1a\n', '不是 PNG'
    p, w, h, depth, ct = 8, 0, 0, 0, 0
    idat = b''
    while p + 8 <= len(data):
        ln = struct.unpack('>I', data[p:p + 4])[0]
        typ = data[p + 4:p + 8]
        chunk = data[p + 8:p + 8 + ln]
        if typ == b'IHDR':
            w, h, depth, ct = struct.unpack('>IIBB', chunk[:10])
        elif typ == b'IDAT':
            idat += chunk
        elif typ == b'IEND':
            break
        p += 12 + ln
    assert depth == 8, '仅支持 8-bit'
    ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ct]
    raw = zlib.decompress(idat)
    stride = w * ch
    out = bytearray(w * h * 4)
    prev = bytearray(stride)
    q = 0
    for y in range(h):
        f = raw[q]
        q += 1
        cur = bytearray(raw[q:q + stride])
        q += stride
        for x in range(stride):
            a = cur[x - ch] if x >= ch else 0
            b = prev[x]
            c = prev[x - ch] if x >= ch else 0
            if f == 1:
                cur[x] = (cur[x] + a) & 255
            elif f == 2:
                cur[x] = (cur[x] + b) & 255
            elif f == 3:
                cur[x] = (cur[x] + ((a + b) >> 1)) & 255
            elif f == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                cur[x] = (cur[x] + pr) & 255
        for x in range(w):
            s, d = x * ch, (y * w + x) * 4
            if ct == 6:
                out[d:d + 4] = cur[s:s + 4]
            elif ct == 2:
                out[d:d + 3] = cur[s:s + 3]
                out[d + 3] = 255
            elif ct == 0:
                out[d] = out[d + 1] = out[d + 2] = cur[s]
                out[d + 3] = 255
            elif ct == 4:
                out[d] = out[d + 1] = out[d + 2] = cur[s]
                out[d + 3] = cur[s + 1]
        prev = cur
    return w, h, bytes(out), ct


# ---------------------------------------------------------------- TGA 解码
def parse_tga(data):
    assert len(data) >= 18, 'TGA 过短'
    imgtype = data[2]
    w, h = struct.unpack('<HH', data[12:16])
    depth, desc = data[16], data[17]
    px = data[18:]
    return {'type': imgtype, 'w': w, 'h': h, 'depth': depth, 'desc': desc, 'px': px}


def tga_rgba_at(t, x, y):
    """encodeTGA 以 BGRA 写入、行序从 y=h-1 递减 → 左下原点。按源图坐标取回 RGBA。"""
    k = (t['h'] - 1 - y) * t['w'] + x
    b, g, r, a = t['px'][k * 4:k * 4 + 4]
    return (r, g, b, a)


# ---------------------------------------------------------------- 算法参考实现
def labpbr_to_mers(r, g, b, a, metal='binary', sss=True):
    s = r / 255
    rough = (1 - s) ** 2
    m = 1 if g >= 230 else 0
    emis = 0 if a == 255 else a / 254
    sv = (b - 65) / 190 if b >= 65 else 0
    if not sss:
        sv = 0
    if m > sv:
        sv = 0
    elif sv > m:
        m = 0
    return tuple(js_round(max(0, min(1, v)) * 255) for v in (m, emis, rough, sv))


def split_normal(r, g, b, a, flip=False):
    ng = 255 - g if flip else g
    x, y = r / 255 * 2 - 1, ng / 255 * 2 - 1
    z = math.sqrt(max(0, 1 - x * x - y * y))
    return (r, ng, js_round((z * 0.5 + 0.5) * 255))


# ---------------------------------------------------------------- 读文件
with zipfile.ZipFile(PACK) as z:
    pack = {i.filename: z.read(i.filename) for i in z.infolist()}
with zipfile.ZipFile(DEMO) as z:
    demo = {i.filename: z.read(i.filename) for i in z.infolist()}
with open(os.path.join(OUT, 'report.json'), encoding='utf-8') as f:
    report = json.load(f)

names = sorted(pack.keys())

# ---------------------------------------------------------------- A 包结构
ck('A', 'ZIP 可解析且非零文件', len(pack) > 0, f'{len(pack)} 个文件')
ck('A', 'manifest.json 存在', 'manifest.json' in pack)
mani = json.loads(pack['manifest.json'])
ck('A', 'manifest.format_version == 2', mani.get('format_version') == 2, mani.get('format_version'))
ck('A', "capabilities 含 'pbr'", 'pbr' in mani.get('capabilities', []), mani.get('capabilities'))
ck('A', 'modules[0].type == resources',
   mani.get('modules', [{}])[0].get('type') == 'resources')
ck('A', 'header/modules uuid 均存在且不重复',
   bool(mani['header'].get('uuid')) and bool(mani['modules'][0].get('uuid'))
   and mani['header']['uuid'] != mani['modules'][0]['uuid'])
_icon = pack.get('pack_icon.png', b'')
ck('A', 'pack_icon.png 是有效 PNG', _icon[:8] == b'\x89PNG\r\n\x1a\n')
_iw, _ih = struct.unpack('>II', _icon[16:24]) if len(_icon) >= 24 and _icon[:8] == b'\x89PNG\r\n\x1a\n' else (0, 0)
ck('A', '封面唯一（根目录只有一个 pack_icon.*）',
   len([n for n in names if n.lower().startswith('pack_icon.')]) == 1,
   [n for n in names if n.lower().startswith('pack_icon.')])
ck('A', '封面 128×128 正方形且边长为 2 的幂（基岩 CPACKICON）',
   _iw == 128 and _ih == 128 and _iw & (_iw - 1) == 0, f'{_iw}x{_ih}')
ck('A', '没有 _mer.tga（MER 与 MERS 互斥，官方用 MERS）',
   not any(n.endswith('_mer.tga') for n in names))
_expected_json = ['manifest.json', 'pbr/global.json', '_pbr2vv_report.json']
_loc = report.get('localization') or {}
if _loc.get('enabled'):
    _expected_json.append('texts/languages.json')
ck('A', '没有 .texture_set.json 之外的 JSON 顶层杂项',
   sorted(n for n in names if n.endswith('.json')) ==
   sorted(_expected_json + [n for n in names if n.endswith('.texture_set.json')]))

# ---------------------------------------------------------------- A2 多语言简介模板
if _loc.get('enabled'):
    _langs = json.loads(pack.get('texts/languages.json', b'{}'))
    ck('A2', 'languages.json 声明 zh_CN / en_US',
       'zh_CN' in _langs and 'en_US' in _langs, _langs)
    for _lf in ('texts/zh_CN.lang', 'texts/en_US.lang'):
        _ltxt = pack.get(_lf, b'').decode('utf-8', 'replace')
        ck('A2', f'{_lf} 含 pack.name / pack.description 覆盖键',
           'pack.name=' in _ltxt and 'pack.description=' in _ltxt)
        ck('A2', f'{_lf} 无裸换行（简介转义为字面 \\n）',
           len(_ltxt.splitlines()) <= 4)
        ck('A2', f'{_lf} 保留 Java 原介绍 PBR2VV 演示包',
           'PBR2VV 演示包' in _ltxt)
    ck('A2', '报告 localization.files 三件套齐全',
       set(_loc.get('files', [])) == {'texts/languages.json','texts/zh_CN.lang','texts/en_US.lang'},
       _loc.get('files'))

# ---------------------------------------------------------------- B texture_set
tsnames = [n for n in names if n.endswith('.texture_set.json')]
ck('B', 'texture_set.json 数量 == 已转换组数',
   len(tsnames) == report['output']['converted'], f"{len(tsnames)} vs {report['output']['converted']}")
for n in tsnames:
    base = os.path.basename(n)[:-len('.texture_set.json')]
    ts = json.loads(pack[n])
    ck('B', f'{base}: format_version=1.21.30', ts.get('format_version') == '1.21.30', ts.get('format_version'))
    body = ts.get('minecraft:texture_set', {})
    ck('B', f'{base}: color 指向自身且无扩展名',
       body.get('color') == base and '.' not in str(body.get('color')), body.get('color'))
    ck('B', f'{base}: MERS 字段值 = color+"_mers"',
       body.get('metalness_emissive_roughness_subsurface') == base + '_mers',
       body.get('metalness_emissive_roughness_subsurface'))
    ck('B', f'{base}: 不含 MER 字段（互斥）', 'metalness_emissive_roughness' not in body)
    ck('B', f'{base}: normal/heightmap 不同时出现',
       not ('normal' in body and 'heightmap' in body))
    if 'normal' in body:
        ck('B', f'{base}: normal 值无扩展名',
           body['normal'] == base + '_normal' and '.' not in body['normal'], body['normal'])
    ck('B', f'{base}: 引用的贴图实体都存在',
       f'textures/blocks/{base}.png' in pack and f'textures/blocks/{base}_mers.tga' in pack)

# ---------------------------------------------------------------- D 输入 PNG 规格（canvas 预乘 alpha 检测）
SPEC_S = {
    'demo_metal_s': (210, 231, 20, 0),
    'demo_glow_s': (90, 40, 200, 254),
    'demo_stone_s': (30, 20, 30, 0),
}
SPEC_N = {'demo_metal_n': (128, 128, 255, 140)}
for base, want in {**SPEC_S, **SPEC_N}.items():
    p = f'assets/minecraft/textures/block/{base}.png'
    w, h, px, ct = decode_png(demo[p])
    got = tuple(px[0:4])
    ck('D', f'输入 {base}.png 首像素 == 源码规格 {want}',
       got == want, f'实际 {got}，颜色类型 ct={ct}；不一致通常因 makePNG 经 canvas 预乘 alpha')

# ---------------------------------------------------------------- C TGA 头 + 逐像素
CUSTOM = {'demo_metal': 'iron_block', 'demo_glow': 'glowstone',
          'demo_stone': 'stone', 'demo_plain': 'dirt'}
for src, dst in CUSTOM.items():
    sp = f'assets/minecraft/textures/block/{src}_s.png'
    if sp not in demo:
        continue
    w, h, px, ct = decode_png(demo[sp])
    tp = f'textures/blocks/{dst}_mers.tga'
    t = parse_tga(pack[tp])
    ck('C', f'{dst}_mers.tga: 头 type=2/depth=32/desc=8',
       t['type'] == 2 and t['depth'] == 32 and t['desc'] == 8,
       f"type={t['type']} depth={t['depth']} desc={t['desc']}")
    ck('C', f'{dst}_mers.tga: 尺寸与 _s 一致且数据长度正确',
       (t['w'], t['h']) == (w, h) and len(t['px']) == w * h * 4,
       f"tga={t['w']}x{t['h']}/{len(t['px'])}B  src={w}x{h}")
    bad = 0
    first_expect = first_got = None
    for y in range(h):
        for x in range(w):
            j = (y * w + x) * 4
            exp = labpbr_to_mers(px[j], px[j + 1], px[j + 2], px[j + 3])
            got = tga_rgba_at(t, x, y)
            if x == 0 and y == 0:
                first_expect, first_got = exp, got
            if exp != got:
                bad += 1
    ck('C', f'{dst}_mers.tga: 全 {w * h} 像素逐点符合换算公式',
       bad == 0, f'不一致 {bad} 像素；首像素期望 RGBA={first_expect} 实际={first_got}')

# 法线
np_ = 'assets/minecraft/textures/block/demo_metal_n.png'
if np_ in demo:
    w, h, px, ct = decode_png(demo[np_])
    t = parse_tga(pack['textures/blocks/iron_block_normal.tga'])
    ck('C', 'iron_block_normal.tga: 头 type=2/depth=32/desc=8',
       t['type'] == 2 and t['depth'] == 32 and t['desc'] == 8)
    bad = 0
    for y in range(h):
        for x in range(w):
            j = (y * w + x) * 4
            exp = split_normal(px[j], px[j + 1], px[j + 2], px[j + 3]) + (255,)
            if tga_rgba_at(t, x, y) != exp:
                bad += 1
    ck('C', 'iron_block_normal.tga: 全像素符合 splitNormal（Z 重建 / A=255）', bad == 0,
       f'不一致 {bad} 像素')

# ---------------------------------------------------------------- E 映射 / 回退 / 报告
ck('E', '输出使用自定义映射后的目标名，无 demo_* 残留',
   not any('demo_' in n for n in names))
for dst in ('iron_block', 'glowstone', 'stone'):
    ck('E', f'{dst} 三件套齐全',
       all(f'textures/blocks/{dst}{suf}' in pack
           for suf in ('.png', '_mers.tga', '.texture_set.json')))
ck('E', 'dirt 只有基色（无 _s 不走 MERS）',
   'textures/blocks/dirt.png' in pack and 'textures/blocks/dirt_mers.tga' not in pack)

fb = json.loads(pack['pbr/global.json'])
ck('E', 'pbr/global.json format_version=1.21.40', fb.get('format_version') == '1.21.40')
fbs = fb.get('minecraft:pbr_fallback_settings', {})
ck('E', '回退覆盖 blocks/actors/particles/items 四类且 MERS 默认值正确',
   sorted(fbs.keys()) == ['actors', 'blocks', 'items', 'particles'] and
   all(fbs[k]['global_metalness_emissive_roughness_subsurface'] == [0, 0, 255, 0] for k in fbs))

ck('E', 'report.output.files 与实际包内文件数一致',
   report['output']['files'] == len(pack),
   f"报告 {report['output']['files']} vs 实际 {len(pack)}")
ck('E', 'report.mapping.customHits == 4',
   report['mapping']['customHits'] == 4, report['mapping'])
ck('E', 'report.output.converted == texture_set 数',
   report['output']['converted'] == len(tsnames))
ck('E', 'report.output.normalMaps == 含 normal 的 texture_set 数',
   report['output']['normalMaps'] ==
   sum(1 for n in tsnames if 'normal' in json.loads(pack[n])['minecraft:texture_set']))
ck('E', 'report.icon 标注为中性占位（演示包不带自造假封面）',
   report.get('icon', {}).get('source') == 'placeholder', report.get('icon'))
ck('E', 'report.icon 尺寸为 128×128',
   report.get('icon', {}).get('width') == 128 and report.get('icon', {}).get('height') == 128,
   report.get('icon'))
conv = report.get('conversion', {})
ck('E', 'report.conversion 含时间/工具/选项',
   bool(conv.get('convertedAt')) and 'PBR2VV' in conv.get('tool', '')
   and len(conv.get('options', {})) >= 7,
   {'tool':conv.get('tool'),'convertedAt':conv.get('convertedAt')})
ck('E', 'manifest.description 含 Java 介绍 + 转换记录',
   'PBR2VV 演示包' in mani['header'].get('description','')
   and 'PBR2VV 转换记录' in mani['header'].get('description','')
   and '转换时间' in mani['header'].get('description',''),
   mani['header'].get('description','')[:120])
ck('E', 'manifest.description 与 report.conversion.manifestDescription 一致',
   mani['header'].get('description') == conv.get('manifestDescription'))
ck('E', 'report.conversion.sourceDescription = 演示包介绍',
   conv.get('sourceDescription') == 'PBR2VV 演示包'
   and conv.get('sourceDescriptionFromMeta') is True)
ck('E', '包内 _pbr2vv_report.json 与导出 report.json 完全一致',
   json.loads(pack['_pbr2vv_report.json']) == report)

# ---------------------------------------------------------------- 汇总
result = {
    'pack': PACK, 'fileCount': len(pack), 'names': names,
    'total': len(checks), 'passed': sum(1 for c in checks if c['ok']),
    'failed': [c for c in checks if not c['ok']], 'checks': checks
}
with open(os.path.join(OUT, 'pack_check.json'), 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"[包校验] {result['passed']}/{result['total']} 通过 · {len(pack)} 个文件")
for c in result['failed']:
    print(f"  FAIL [{c['group']}] {c['name']} :: {c['detail']}")
print('文件清单：')
for n in names:
    print('  ' + n)
