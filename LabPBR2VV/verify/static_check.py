#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""static_check.py — 工程静态一致性检查（纯网页版形态，无需 Android SDK / 无需浏览器）

2026-11-15 更新：APK 工程（android/ 与 mapping/native_adapter.js、sync_assets.py）
已按用户要求移除。原 A/D/E 组对双端引擎与 Android 清单的断言不再适用，
改为检查「单文件离线自洽」+「APK 已移除」守卫；B/C/修复点组保留。
"""
import json
import os
import re
import subprocess
import tempfile

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WEB = os.path.join(BASE, 'LabPBR2VV.html')
MAPJSON = os.path.join(BASE, 'name_map.json')
MAPPING = os.path.join(BASE, 'mapping')

checks = []


def ck(group, name, ok, detail=''):
    checks.append({'group': group, 'name': name, 'ok': bool(ok), 'detail': str(detail)})


web = open(WEB, encoding='utf-8').read()

# A 单文件离线自洽（APK 移除后，LabPBR2VV.html 就是唯一交付引擎）
scripts = re.findall(r'<script>(.*?)</script>', web, re.S)
ck('A', '网页版只有 1 个内联 <script>',
   web.count('<script') == 1 and web.count('</script>') == 1 and len(scripts) == 1)
ck('A', '无外部脚本/样式引用',
   not re.search(r'<script[^>]*\bsrc=|<link[^>]*\bhref=', web))
ck('A', '无网络 API',
   not re.search(r'\bfetch\s*\(|XMLHttpRequest|new WebSocket|\bimport\s*\(', web))
ck('A', '无任何 http(s) 外部 URL', 'http://' not in web and 'https://' not in web)
ck('A', '不含原生桥代码', 'AndroidBridge' not in web)
ck('A', '单文件即完整转换器',
   all(k in web for k in ('function convert(', 'function buildDemo(',
                          'function decodePNG(', 'function encodeTGA(')))

# B JS 语法
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
    f.write(scripts[0] if scripts else '')
    tmp = f.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
ck('B', '网页版 JS 通过 node --check', r.returncode == 0, r.stderr.strip()[:200])
os.unlink(tmp)

# C 映射表（M3 产物，与 APK 无关，必须保留且可复现）
builtin = json.loads(re.search(r'const BUILTIN_MAP = (\{.*?\});', web, re.S).group(1))
mapjson = json.load(open(MAPJSON, encoding='utf-8'))
size = int(re.search(r'const BUILTIN_MAP_SIZE = (\d+);', web).group(1))
ck('C', '内置表条数与 name_map.json 一致（>=445）', len(builtin) == len(mapjson) >= 445, len(builtin))
ck('C', 'BUILTIN_MAP_SIZE 与实际条数一致', size == len(builtin), size)
ck('C', '与 name_map.json 完全一致', builtin == mapjson)
ck('C', 'mapping/ 生成脚本与数据源仍在',
   os.path.isfile(os.path.join(MAPPING, 'build_map.py')) and
   all(os.path.isfile(os.path.join(MAPPING, x)) for x in
       ('texturesJE.js', 'texturesBE.js', 'vibrantVisuals.js',
        'name_map_meta.json', 'unresolved.json')))

# D 历次修复点必须仍在（防止后续改回）
# 材质贴图通道绝不能经过 canvas（alpha 预乘会毁掉 _s）；
# 但封面 JPEG 的浏览器兜底解码是安全的（封面无 alpha=0 语义），故按函数体精确检查
_mk = web[web.index('async function makePNG('):web.index('/* ---- 封面规整')]
_dp = web[web.index('async function decodePNG('):web.index('async function encodePNGBytes(')]
ck('D', '材质 PNG 编解码均不经过 canvas',
   "createElement('canvas')" not in _mk and "createElement('canvas')" not in _dp
   and '.toBlob(' not in web and 'encodePNGBytes' in web)
_di = web[web.index('async function decodeIcon('):web.index('function placeholderIcon(')]
ck('D', 'canvas 仅用于封面图像兜底解码',
   "createElement('canvas')" in _di and 'getImageData' in _di)
ck('D', 'PNG 编码用 CompressionStream(deflate)', "new CompressionStream('deflate')" in web)
ck('D', '报告回填 output.files', 'REPORT.output.files = E.length' in web)
ck('D', '启动自检同时检测压缩/解压流',
   "new DecompressionStream('deflate-raw'); new CompressionStream('deflate')" in web)
ck('D', '法线变量可重新赋值（修复 const 报错）',
   re.search(r'\blet nrm\s*=', web) is not None)
ck('D', '输出侧固定生成 pack_icon.png（根目录唯一）',
   "const iconFile = 'pack_icon.png'" in web)
ck('D', '默认引擎版本兼容网易版', 'value="1,21,120" selected' in web)
ck('D', '扫描入口过滤 macOS AppleDouble/空格名',
   'function isJunkPath' in web and '__MACOSX' in web and 'AppleDouble' in web)
ck('D', '基色复制前校验 PNG 头', 'const okPNG' in web and 'invalidPng++' in web)
ck('D', '输出名去重（防重复 ZIP 条目）',
   'const emitted = new Set()' in web and 'dupSkipped' in web)
ck('D', '叠加模式跳过 pbr/global.json 全局单例',
   'id="optStack"' in web and 'opt.stack' in web and '全局单例' in web)
ck('D', '自动识别包名（pack.mcmeta / 文件名兜底）',
   'async function detectPackName' in web and 'function cleanPackName' in web)
ck('D', '封面规整为 128×128 正方形 2 幂（基岩 CPACKICON）',
   'const ICON_SIZE = 128' in web and 'function normalizeIcon' in web and
   'function makePNGRGBA' in web)
ck('D', '封面支持自定义上传，且占位为中性图而非棋盘',
   'id="iconfile"' in web and 'function placeholderIcon' in web and
   'CUSTOM_ICON' in web and '[124,179,66]' not in web)
ck('D', '封面同时认 Java pack.png 与基岩 pack_icon.png',
   'pack\\.png$/i' in web and 'pack_icon\\.png$/i' in web)

ck('D', 'Java 介绍同步到基岩版 header.description',
   'function cleanDescription' in web and 'function descText' in web
   and 'description: manifestDesc' in web and 'sourceDescription' in web)
ck('D', '转换记录含时间/工具/选项',
   'convertedAt:' in web and 'convertedAtLocal:' in web
   and 'PBR2VV 转换记录' in web and 'const convRecord' in web)
ck('D', '多语言简介模板开关存在且默认勾选',
   'id="optI18n" checked' in web and 'opt.i18n' in web and 'localizedDescription' in web)
ck('D', '输出 texts/languages.json + zh_CN/en_US .lang 覆盖显示',
   all(k in web for k in ('texts/languages.json', 'texts/zh_CN.lang',
                          'texts/en_US.lang', 'pack.name=', 'pack.description=',
                          "'zh_CN','en_US'")))
ck('D', '.lang 换行转义为字面 \\n（toLangValue）',
   'function toLangValue' in web and "replace(/\\n/g, '\\\\n')" in web)
ck('D', '报告 localization 记录',
   'localization:' in web and 'files: langFiles' in web)
# E 目录与格式修复（2026-11-16：盔甲/地图落错目录、植物类应写 tga）
ck('E', '目录推断沿用 Java 原目录（不再一律塞 blocks）',
   r'/\/textures\/(.+)\/[^\/]+$/' in web and 'const PBR_DIRS' in web)
ck('E', '非 PBR 目录显式跳过并计数',
   'skippedNoPBR' in web and 'skippedNonPBRDir' in web)
ck('E', '官方仅 tga 的基色按 tga 输出',
   'const TGA_BASE' in web and "outBase + '.tga'" in web and 'tgaBaseColors' in web)
ck('E', 'TGA 名单覆盖树叶/蕨/丁香/高草',
   all(n in web for n in ("'leaves_oak'", "'fern'", "'double_plant_syringa_top'", "'double_plant_grass_top'")))
ck('E', 'Java 1.21.2+ 装备目录 → models/armor（盔甲）',
   'const ARMOR_DIRS' in web and 'entity/equipment/humanoid_leggings' in web
   and 'ARMOR_MAT_BABY' in web and "chainmail:'chain'" in web
   and 'turtle_scute:' in web and 'skip:true' in web and 'skippedArmorLayer' in web)
ck('E', 'entity 子目录（床等）按前缀放行 + 皮革盔甲 tga',
   'function isPBRDir' in web and "dir.startsWith('entity/')" in web
   and "'leather_1','leather_2','leather_baby'" in web
   and "dir === 'entity/bed' && base === 'light_gray'" in web)
ck('E', 'Java pack_format 识别（版本→目录代际）',
   'const JAVA_PACK_FORMATS' in web and 'function javaVersionOf' in web
   and 'function javaEraOf' in web and 'sourcePackFormat' in web and 'sourceEra' in web)
ck('E', '盔甲/末地/耕地/睡莲/单双格花映射已补录',
   all(p in web for p in ('"end_portal_frame_side":"endframe_side"',
                          '"farmland":"farmland_dry"',
                          '"lily_pad":"waterlily"',
                          '"peony_top":"double_plant_paeonia_top"',
                          '"lilac_top":"double_plant_syringa_top"',
                          '"large_fern_top":"double_plant_fern_top"',
                          '"sunflower_front":"double_plant_sunflower_front"',
                          '"diamond_layer_1":"diamond_1"')))
ck('D', '材质通道可视化预览（点击表格行 → MERS 四通道）',
   'function previewGroup' in web and 'function paintRGBA' in web
   and 'onclick="previewGroup' in web and 'id="pv-imgs"' in web and 'imgs4' in web)
ck('D', '预览用 putImageData 直写（不经 canvas 预乘，不污染材质数据）',
   'putImageData' in web and "ctx.createImageData(w, h)" in web)
ck('D', 'PNG 解码非预乘（逐字节 RGBA，不经 canvas）',
   'async function decodePNG' in web and 'out[d]=cur[s]' in web
   and 'out[d+3]=cur[s+3]' in web)

# E APK 已移除（当前项目形态守卫，防止旧文件被误放回）
ck('E', 'android/ 工程已移除', not os.path.exists(os.path.join(BASE, 'android')))
ck('E', 'APK 专用适配脚本已移除',
   not os.path.exists(os.path.join(MAPPING, 'native_adapter.js')) and
   not os.path.exists(os.path.join(MAPPING, 'sync_assets.py')))

out = os.path.join(os.path.dirname(__file__), 'out', 'static_check.json')
with open(out, 'w', encoding='utf-8') as f:
    json.dump({'total': len(checks), 'passed': sum(1 for c in checks if c['ok']),
               'failed': [c for c in checks if not c['ok']], 'checks': checks},
              f, ensure_ascii=False, indent=2)
print(f"[静态检查] {sum(1 for c in checks if c['ok'])}/{len(checks)} 通过")
for c in checks:
    if not c['ok']:
        print(f"  FAIL [{c['group']}] {c['name']} :: {c['detail']}")
raise SystemExit(0 if all(c['ok'] for c in checks) else 1)
