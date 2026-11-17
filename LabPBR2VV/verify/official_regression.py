#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
official_regression.py — 用 Mojang 官方样例包实物做 MERS 回归

数据源：bedrock-samples-v1.26.70.23-preview-full.zip（3,171 组）
校验两类事情：
  1) 复核 12/13 号文档里从官方包得出的结论（位深、schema、命名、配对、manifest）
  2) 设计文档 §8 的「集成测试」：反解官方 MERS → 逆推 LabPBR _s → 再用
     labpbrToMers 转回，量化 round-trip 误差，判定哪些通道可复现、哪些必然有损

输出：out/official_regression.json
"""
import json
import math
import os
import struct
import zipfile
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
ZIP = os.environ.get(
    'OFFICIAL_ZIP',
    '/root/.codebuddy/artifact/2f8a7d30-9c21-4f0b-1d72-5249b0df3000/official.zip')


def js_round(v):
    return np.floor(v + 0.5).astype(np.int32)


def inv_s_from_mers(M, E, R, S, quantize):
    """由官方 MERS 反推 LabPBR _s 的 (r,g,b,a)。
    r: roughness=(1-s)^2 → s=1-sqrt(rough)
    g: 二值策略下只有金属(255)/介电质(0) 两种可表达值
    b: SSS 段 65..255
    a: 自发光 0..254（255 是保留值）
    """
    r = (1.0 - np.sqrt(R / 255.0)) * 255.0
    g = np.where(M >= 128, 255.0, 0.0)
    b = np.where(S > 0, 65.0 + S / 255.0 * 190.0, 0.0)
    a = E / 255.0 * 254.0
    if quantize:                     # _s 实际是 8-bit 贴图，必须量化
        r, g, b, a = (js_round(x) for x in (r, g, b, a))
    return r, g, b, a


def labpbr_to_mers_np(r, g, b, a):
    """与 LabPBR2VV.html 的 labpbrToMers 逐行等价的向量化实现"""
    rough = (1.0 - r / 255.0) ** 2
    metal = np.where(g >= 230, 1.0, 0.0)
    emis = np.where(a == 255, 0.0, a / 254.0)
    sss = np.where(b >= 65, (b - 65.0) / 190.0, 0.0)
    metal2 = np.where(metal > sss, metal, 0.0)      # 金属/SSS 互斥，取大值
    sss2 = np.where(sss > metal, sss, 0.0)
    return np.stack([js_round(np.clip(v, 0, 1) * 255.0)
                     for v in (metal2, emis, rough, sss2)], axis=-1)


with zipfile.ZipFile(ZIP) as z:
    allnames = z.namelist()
    mers = [n for n in allnames if n.lower().endswith('_mers.tga')]
    tsets = [n for n in allnames if n.lower().endswith('.texture_set.json')]
    mers_set = set(mers)
    tset_set = set(tsets)

    depth_cnt = Counter()
    desc_cnt = Counter()
    type_cnt = Counter()
    dir_cnt = Counter()
    size_cnt = Counter()
    schema_cnt = Counter()
    field_cnt = Counter()
    missing_pair = []
    ref_broken = []
    ext_in_value = []
    desc40 = []               # 0x28 = 上左原点(y_top=1) + 8 alpha bits，非主流
    const_array_refs = []     # MERS 字段写常量数组而非贴图名（规范允许的写法）
    cross_dir_orphans = []    # MERS 与同名 texture_set 不在同一目录
    orphan_mers = []          # 完全没有 texture_set 引用的 MERS
    color_only_sets = []      # 只有 color、没有 MERS 层的 texture_set

    # 通道直方图与互斥统计
    hist = [np.zeros(256, dtype=np.int64) for _ in range(4)]
    total_px32 = 0
    metal_and_sss = 0
    metal_mid = 0            # 金属度非 0/255 的像素（连续金属度）
    rt = {q: {'n': 0, 'sum': np.zeros(4), 'max': np.zeros(4), 'within1': np.zeros(4)}
          for q in (False, True)}

    first_pixel = None
    iron_sum = None

    for name in mers:
        d = z.read(name)
        imgtype, depth, desc = d[2], d[16], d[17]
        w, h = struct.unpack('<HH', d[12:16])
        type_cnt[imgtype] += 1
        depth_cnt[depth] += 1
        desc_cnt[desc] += 1
        if desc == 40:
            desc40.append(name)
        dir_cnt[name.split('/textures/')[-1].split('/')[0] if '/textures/' in name else '?'] += 1
        size_cnt[f'{w}x{h}'] += 1

        px = d[18:]
        bpp = 4 if depth == 32 else 3
        if len(px) < w * h * bpp:
            continue
        arr = np.frombuffer(px[:w * h * bpp], dtype=np.uint8).reshape(h, w, bpp)
        # TGA 是 BGRA（24-bit 时 BGR），按源图语义还原成 RGBA
        if bpp == 4:
            rgba = arr[:, :, [2, 1, 0, 3]]
        else:
            rgba = np.dstack([arr[:, :, [2, 1, 0]],
                              np.zeros((h, w, 1), dtype=np.uint8)])

        if name.endswith('blocks/iron_block_mers.tga'):
            first_pixel = tuple(int(v) for v in rgba[0, 0])
            iron_sum = tuple(float(v) for v in rgba.reshape(-1, 4).mean(axis=0))

        for c in range(4):
            hist[c] += np.bincount(rgba[:, :, c].reshape(-1), minlength=256)

        if bpp == 4:
            M = rgba[:, :, 0].astype(np.float64)
            E = rgba[:, :, 1].astype(np.float64)
            R = rgba[:, :, 2].astype(np.float64)
            S = rgba[:, :, 3].astype(np.float64)
            npx = M.size
            total_px32 += npx
            metal_and_sss += int(np.count_nonzero((M > 0) & (S > 0)))
            metal_mid += int(np.count_nonzero((M > 0) & (M < 255)))

            for q in (False, True):
                r, g, b, a = inv_s_from_mers(M, E, R, S, q)
                back = labpbr_to_mers_np(r, g, b, a).astype(np.float64)
                orig = np.stack([M, E, R, S], axis=-1)
                diff = np.abs(back - orig)
                t = rt[q]
                t['n'] += npx
                t['sum'] += diff.reshape(-1, 4).sum(axis=0)
                t['max'] = np.maximum(t['max'], diff.reshape(-1, 4).max(axis=0))
                t['within1'] += (diff <= 1).reshape(-1, 4).sum(axis=0)

        # 配对检查（同目录优先；跨目录同名单独归类）
        base = name[:-len('_mers.tga')]
        expect_ts = base + '.texture_set.json'
        if expect_ts not in tset_set:
            stem = base.rsplit('/', 1)[-1]
            elsewhere = [t for t in tsets if t.endswith('/' + stem + '.texture_set.json')]
            if elsewhere:
                cross_dir_orphans.append({'mers': name, 'textureSetElsewhere': elsewhere})
            else:
                orphan_mers.append(name)
                missing_pair.append(expect_ts)

    for name in tsets:
        try:
            ts = json.loads(z.read(name))
        except Exception as e:
            ref_broken.append(f'{name}: JSON 解析失败 {e}')
            continue
        schema_cnt[str(ts.get('format_version'))] += 1
        body = ts.get('minecraft:texture_set', {})
        for k in body:
            field_cnt[k] += 1
        for k, v in body.items():
            if isinstance(v, str) and (v.endswith('.tga') or v.endswith('.png')):
                ext_in_value.append(f'{name}:{k}={v}')
        base = name[:-len('.texture_set.json')]
        ref = body.get('metalness_emissive_roughness_subsurface')
        if isinstance(ref, list):
            const_array_refs.append({'name': name, 'value': ref})
        elif isinstance(ref, str):
            expect = base.rsplit('/', 1)[0] + '/' + ref + '.tga'
            if expect not in mers_set:
                ref_broken.append(f'{name}: 引用 {expect} 不存在')
        else:
            color_only_sets.append(name)

    manifest = json.loads(z.read('resource_pack/manifest.json'))
    has_mer = [n for n in allnames if n.lower().endswith('_mer.png') or n.lower().endswith('_mer.tga')]


def pct(a, b):
    return round(float(a) / float(b) * 100, 2) if b else 0.0


rt_out = {}
for q in (False, True):
    t = rt[q]
    key = 'quantized_8bit' if q else 'float_exact'
    rt_out[key] = {
        'pixels': t['n'],
        'channels': ['metalness(R)', 'emissive(G)', 'roughness(B)', 'subsurface(A)'],
        'meanAbsError': [round(float(v) / t['n'], 4) for v in t['sum']],
        'maxAbsError': [int(v) for v in t['max']],
        'withinOnePct': [pct(v, t['n']) for v in t['within1']]
    }

result = {
    'source': os.path.basename(ZIP),
    'counts': {
        'mersTga': len(mers), 'textureSetJson': len(tsets),
        'merLegacy': len(has_mer), 'missingPairs': len(missing_pair),
        'brokenReferences': len(ref_broken), 'valuesWithExtension': len(ext_in_value),
        'constArrayMersRefs': len(const_array_refs), 'colorOnlyTextureSets': len(color_only_sets),
        'crossDirOrphans': len(cross_dir_orphans), 'orphanMers': len(orphan_mers)
    },
    'tga': {
        'imageType': dict(type_cnt), 'depth': dict(depth_cnt), 'descriptor': dict(desc_cnt),
        'topSizes': dict(size_cnt.most_common(8)), 'byDir': dict(dir_cnt)
    },
    'textureSet': {'formatVersion': dict(schema_cnt), 'fields': dict(field_cnt)},
    'manifest': {
        'formatVersion': manifest.get('format_version'),
        'minEngineVersion': manifest.get('header', {}).get('min_engine_version'),
        'capabilities': manifest.get('capabilities', '<不存在>')
    },
    'ironBlock': {
        'firstPixelRGBA': first_pixel,
        'channelMeansRGBA': iron_sum,
        'doc13Record': {'R': 191.0, 'G': 0.0, 'B': 136.7, 'A': 0.0,
                        'firstPixel': [191, 0, 176, 0]}
    },
    'channelHistogramTop': [
        {['metalness', 'emissive', 'roughness', 'subsurface'][c]:
         {str(v): int(hist[c][v]) for v in np.argsort(hist[c])[-5:][::-1]}}
        for c in range(4)
    ],
    'consistency': {
        'px32': total_px32,
        'metalAndSubsurfaceBothNonZero': metal_and_sss,
        'continuousMetalnessPixels': metal_mid,
        'continuousMetalnessPct': pct(metal_mid, total_px32)
    },
    'roundTrip': rt_out,
    'anomalies': {
        'descriptor40_topLeftOrigin': desc40,
        'descriptor40Count': len(desc40),
        'missingPairs': missing_pair,
        'brokenReferences': ref_broken,
        'valuesWithExtension': ext_in_value,
        'constArrayMersRefs': const_array_refs,
        'colorOnlyTextureSets': color_only_sets[:20],
        'crossDirOrphans': cross_dir_orphans,
        'orphanMers': orphan_mers
    }
}

with open(os.path.join(OUT, 'official_regression.json'), 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"[官方包回归] {len(mers)} 组 MERS / {len(tsets)} 个 texture_set")
print("位深:", result['tga']['depth'], ' descriptor:', result['tga']['descriptor'])
print("schema:", result['textureSet']['formatVersion'])
print("manifest.capabilities:", result['manifest']['capabilities'])
print("配对缺失:", result['counts']['missingPairs'],
      ' 引用断裂:', result['counts']['brokenReferences'],
      ' 值带扩展名:', result['counts']['valuesWithExtension'])
print("iron_block 首像素 RGBA:", first_pixel, ' 均值:', iron_sum)
print("连续金属度像素:", metal_mid, f'({result["consistency"]["continuousMetalnessPct"]}%)')
print("金属+SSS 同时非零:", metal_and_sss)
for k, v in rt_out.items():
    print(f"round-trip [{k}] meanAbsErr={v['meanAbsError']} max={v['maxAbsError']} within1%={v['withinOnePct']}")
print("descriptor=40（上左原点）:", len(desc40), desc40[:5])
print("配对缺失:", missing_pair[:5])
print("引用断裂:", ref_broken[:5])
