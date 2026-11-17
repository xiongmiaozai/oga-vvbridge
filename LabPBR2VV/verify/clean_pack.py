#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
清洗 PBR2VV 转换产物，使其可安全叠加到已有的 PBR 资源包（如 ENRO）之上。

解决的三个实测问题（详见 17_叠加报错根因与修复.md）：
  1. macOS AppleDouble 垃圾：源 Java 包在 Mac 上打包时带入 58 个 `._xxx.png`
     （176 字节、头为 "Mac OS X" 的资源叉，并非 PNG）。旧 scan() 只按扩展名
     过滤，把它们当成基色原样复制进 textures/blocks/ → 基岩版扫描到非法 PNG
     即报 content error「资源包加载错误」。ENRO 对照包此类文件为 0。
  2. 文件名含空格：资源位置空格会破坏基岩版路径解析。
  3. pbr/global.json（minecraft:pbr_fallback_settings）是全局单例；
     两个都带 capabilities:["pbr"] 的包叠加时，重复定义会冲突。
     --stack 模式移除它，让下层包（ENRO）的全局回退生效。

用法：
  python3.11 clean_pack.py <输入.mcpack> <输出.mcpack> [--stack] [--keep-global]
默认 --stack（面向叠加场景，移除 pbr/global.json）。
--keep-global 则保留（面向单独使用）。
"""
import sys, zipfile, json, os, struct, shutil, collections

PNG_SIG = b'\x89PNG\r\n\x1a\n'


def is_junk(name):
    """返回 (是否删除, 原因)。只删确定有问题/确定冲突的东西。"""
    base = name.split('/')[-1]
    if not base:
        return False, ''
    if '__MACOSX/' in name or name.startswith('__MACOSX/'):
        return True, 'macOS __MACOSX 目录'
    if base.startswith('._'):
        return True, 'macOS AppleDouble 资源叉 ._ 伪文件'
    if base == '.DS_Store':
        return True, 'macOS .DS_Store'
    if ' ' in base:
        return True, '文件名含空格（基岩资源位置不合法）'
    return False, ''


def selftest():
    """内置脏包自检：不依赖任何外部文件，供 run_all.sh 长期回归。"""
    import tempfile, subprocess
    fake = PNG_SIG + b'PBR2VV-SELFTEST' * 4          # 工具只校验 PNG 签名，足够
    junk = b'\x00\x05\x16\x07\x00\x02\x00\x00Mac OS X        '  # AppleDouble 资源叉
    with tempfile.TemporaryDirectory() as d:
        inp, outp = os.path.join(d, 'in.mcpack'), os.path.join(d, 'out.mcpack')
        z = zipfile.ZipFile(inp, 'w', zipfile.ZIP_STORED)
        z.writestr('manifest.json', '{"format_version":2}')
        z.writestr('textures/blocks/good.png', fake)
        z.writestr('textures/blocks/good.texture_set.json',
                   '{"format_version":"1.21.30","minecraft:texture_set":{"color":"good"}}')
        z.writestr('textures/blocks/._junk.png', junk)                 # macOS 垃圾
        z.writestr('__MACOSX/textures/blocks/._foo.png', junk)          # __MACOSX
        z.writestr('textures/blocks/bad name.png', fake)                # 空格名
        z.writestr('textures/blocks/fakepng.png', junk)                 # 非法 PNG 头
        z.writestr('textures/blocks/dup.png', fake)                     # 重复条目
        z.writestr('textures/blocks/dup.png', fake)
        z.writestr('pbr/global.json', '{"format_version":"1.21.40"}')  # 全局单例
        z.writestr('_pbr2vv_report.json', '{"generator":"PBR2VV M0"}')
        z.close()
        r = subprocess.run([sys.executable, __file__, inp, outp, '--stack'],
                           capture_output=True, text=True)
        print(r.stdout.strip())
        if r.returncode != 0:
            print('  selftest 主清洗返回非零:', r.stderr.strip()[:200])
            return 1
        z = zipfile.ZipFile(outp)
        ns = [i.filename for i in z.infolist() if not i.is_dir()]
        checks = {
            '保留合法贴图 good.png': 'textures/blocks/good.png' in ns,
            '保留 good.texture_set.json': 'textures/blocks/good.texture_set.json' in ns,
            '剔除 ._ 垃圾': not any(n.split('/')[-1].startswith('._') for n in ns),
            '剔除 __MACOSX': not any('__MACOSX/' in n for n in ns),
            '剔除空格名': not any(' ' in n.split('/')[-1] for n in ns),
            '剔除非法PNG': not any(n.endswith('.png') and z.read(n)[:8] != PNG_SIG for n in ns),
            '合并重复条目': len(ns) == len(set(ns)),
            '叠加模式移除 pbr/global.json': 'pbr/global.json' not in ns,
            '报告写入 cleanup': 'cleanup' in json.loads(z.read('_pbr2vv_report.json').decode('utf-8-sig')),
        }
        for name, ok in checks.items():
            print(f'  [{"OK" if ok else "FAIL"}] {name}')
        passed = sum(1 for v in checks.values() if v)
        print(f'  clean_pack selftest: {passed}/{len(checks)} 通过')
        return 0 if passed == len(checks) else 1


def main():
    if '--selftest' in sys.argv:
        return selftest()
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = [a for a in sys.argv[1:] if a.startswith('--')]
    if len(args) != 2:
        print('用法: clean_pack.py <输入.mcpack> <输出.mcpack> [--stack|--keep-global]')
        sys.exit(2)
    src, dst = args[0], args[1]
    keep_global = '--keep-global' in flags   # 默认 stack 模式（移除 global.json）
    stack_mode = not keep_global

    zin = zipfile.ZipFile(src)
    names = [n for n in zin.namelist() if not n.endswith('/')]

    removed, reasons = [], {}
    kept = []
    for n in names:
        drop, why = is_junk(n)
        # 兜底：任何 .png 但不是合法 PNG 头，一律剔除
        if not drop and n.lower().endswith('.png'):
            try:
                if zin.read(n)[:8] != PNG_SIG:
                    drop, why = True, '非法 PNG 头（非 PNG 内容）'
            except Exception as e:
                drop, why = True, '读取失败: ' + str(e)[:40]
        # 叠加模式：移除全局单例
        if not drop and stack_mode and n == 'pbr/global.json':
            drop, why = True, '叠加模式：移除全局单例 pbr/global.json（由下层包提供）'
        if drop:
            removed.append(n)
            reasons[why] = reasons.get(why, 0) + 1
        else:
            kept.append(n)

    # 悬空引用复核：被保留的 texture_set 引用的实体必须都还在
    kept_set = set(kept)
    dangling = []
    for n in kept:
        if n.endswith('.texture_set.json'):
            d = json.loads(zin.read(n).decode('utf-8-sig'))
            dr = os.path.dirname(n)
            for k, v in d.get('minecraft:texture_set', {}).items():
                if isinstance(v, str):
                    if not any((dr + '/' + v + e) in kept_set
                               for e in ('.tga', '.png', '.jpg', '.jpeg')):
                        dangling.append((n, k, v))

    # 重复 ZIP 条目统计（同名多条，部分平台加载器会直接报「资源包加载错误」）
    cnt = {}
    for n in names:
        cnt[n] = cnt.get(n, 0) + 1
    dup_names = {n: c for n, c in cnt.items() if c > 1}
    dedup = sum(c - 1 for c in dup_names.values())

    # 写出（store 模式，保持与源包一致），并更新包内报告
    if os.path.exists(dst):
        os.remove(dst)
    zout = zipfile.ZipFile(dst, 'w', zipfile.ZIP_STORED)
    seen = set()
    for n in kept:
        if n in seen:      # 同名条目只保留第一次出现的，消除重复
            continue
        seen.add(n)
        data = zin.read(n)
        if n == '_pbr2vv_report.json':
            try:
                rep = json.loads(data.decode('utf-8-sig'))
                rep['cleanup'] = {
                    'tool': 'PBR2VV clean_pack.py',
                    'mode': 'stack (叠加兼容)' if stack_mode else 'standalone',
                    'removedCount': len(removed),
                    'removedReasons': reasons,
                    'duplicateEntriesCollapsed': dedup,
                    'duplicateNames': sorted(dup_names),
                    'pbrGlobalJson': 'removed (由下层包提供)' if stack_mode else 'kept',
                    'note': '剔除 macOS AppleDouble 伪 PNG / 空格名 / 非法 PNG；合并重复 ZIP 条目；叠加模式另移除 pbr/global.json 全局单例'
                }
                data = json.dumps(rep, ensure_ascii=False, indent=2).encode('utf-8')
            except Exception:
                pass
        zout.writestr(n, data)
    zout.close()
    zin.close()

    # 复验产物
    z = zipfile.ZipFile(dst)
    outnames = [n for n in z.namelist() if not n.endswith('/')]
    bad_png = [n for n in outnames
               if n.lower().endswith('.png') and z.read(n)[:8] != PNG_SIG]
    dot_junk = [n for n in outnames if n.split('/')[-1].startswith('._')
                or '__MACOSX/' in n]
    space_name = [n for n in outnames if ' ' in n.split('/')[-1]]
    bad_json = []
    for n in outnames:
        if n.lower().endswith('.json'):
            try:
                json.loads(z.read(n).decode('utf-8-sig'))
            except Exception as e:
                bad_json.append((n, str(e)[:50]))
    bad_tga = []
    for n in outnames:
        if n.lower().endswith('.tga'):
            d = z.read(n)
            if len(d) < 18 or d[2] not in (2, 10):
                bad_tga.append(n)

    print('=== 清洗结果 ===')
    print(f'  输入文件数      : {len(names)}')
    print(f'  删除            : {len(removed)}')
    for why, c in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f'      {c:3d}  {why}')
    print(f'  重复条目合并    : {dedup}  ({sorted(dup_names)})')
    print(f'  输出文件数      : {len(outnames)}')
    print(f'  输出大小        : {os.path.getsize(dst)/1024/1024:.1f} MB')
    print('  --- 复验 ---')
    print(f'  非法 PNG        : {len(bad_png)}  (应为 0)')
    print(f'  ._ / __MACOSX   : {len(dot_junk)}  (应为 0)')
    print(f'  空格文件名      : {len(space_name)}  (应为 0)')
    dup_out = [n for n, c in collections.Counter(
        [i.filename for i in z.infolist() if not i.is_dir()]).items() if c > 1]
    print(f'  重复 ZIP 条目   : {len(dup_out)}  (应为 0)')
    print(f'  JSON 解析失败   : {len(bad_json)}  (应为 0)')
    print(f'  TGA 头异常      : {len(bad_tga)}  (应为 0)')
    print(f'  texture_set 悬空引用: {len(dangling)}  (应为 0)')
    print(f'  ZIP CRC 全检    : {z.testzip()}')
    print(f'  pbr/global.json : {"保留" if "pbr/global.json" in outnames else "已移除(叠加模式)"}')
    ok = (not bad_png and not dot_junk and not space_name and not bad_json
          and not bad_tga and not dangling and not dup_out and z.testzip() is None)
    print('\n  => ' + ('全部通过，可直接叠加使用' if ok else '仍有问题，需检查'))
    if dangling:
        for d in dangling[:10]:
            print('     DANGLING', d)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
