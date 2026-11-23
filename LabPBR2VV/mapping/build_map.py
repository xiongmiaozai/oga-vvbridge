#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 Java 资源包纹理基名 → 基岩版纹理基名 映射表。

数据源：
  1) Java 侧清单  convertmcpack.net /pages/item_lists/texturesJE.js  （Java 1.21.x）
  2) 基岩侧清单  convertmcpack.net /pages/item_lists/texturesBE.js
  3) 官方实物    Mojang bedrock-samples v1.26.70.23-preview-full.zip
                 的 resource_pack/textures/<dir>/*.texture_set.json

原则：只输出「需要改名」的条目；每条候选必须在权威目标集合中存在才采纳，
      宁可留空让用户自定义，也不做模糊猜测（贴错材质比不映射更糟）。
输出：/workspace/LabPBR2VV/name_map.json  及统计到 stdout。
"""
import re, zipfile, json, collections, os, sys

BASE = "/workspace/LabPBR2VV"
SRC = "/workspace/LabPBR2VV/mapping"
OFFICIAL = "/root/.codebuddy/artifact/2f8a7d30-9c21-4f0b-1d72-5249b0df3000/official.zip"


def lines(p):
    s = open(p, encoding="utf-8", errors="replace").read()
    return [l.strip().rstrip("<br>").strip() for l in s.splitlines()
            if l.strip().endswith("<br>")]


def clean_base(f):
    f = re.sub(r"\.texture_set\.json$|\.png$|\.tga$|\.jpg$|\.json$", "", f)
    # 排除动画元数据条目（*.png.mcmeta 之类），它们不是纹理
    if ".png" in f or ".tga" in f:
        return None
    return f or None


# ---------------- 官方实物补录（MANUAL） ----------------
# 下列名字的自动规则拿不准（长期挂在 unresolved 里），已逐个在
# Mojang bedrock-samples v1.26.70.23-preview-full 实物中确认目标文件存在，
# 属于「有实证的补录」，不是猜测。补录动机：用户实测发现这些贴图转换后
# 在基岩端不生效，逐项核对后确认是目标名不同（而非同名的可直通项）。
#
# 结构：Java 基名 → (基岩基名, 目标所在目录)
MANUAL = {
    # 末地传送门框架：Java end_portal_frame_* → 基岩 endframe_*
    "end_portal_frame_side": ("endframe_side", "blocks"),
    "end_portal_frame_top": ("endframe_top", "blocks"),
    "end_portal_frame_eye": ("endframe_eye", "blocks"),
    # 耕地：Java 用 dry/moist 语义，基岩叫 farmland_dry / farmland_wet
    "farmland": ("farmland_dry", "blocks"),
    "farmland_moist": ("farmland_wet", "blocks"),
    # 睡莲
    "lily_pad": ("waterlily", "blocks"),
    # 玫瑰（1.12 及更早的 Java 基名；1.14+ 叫 poppy，已另有映射）
    "rose": ("flower_rose", "blocks"),
    # 玫瑰丛（双格）
    "rose_bush_top": ("double_plant_rose_top", "blocks"),
    "rose_bush_bottom": ("double_plant_rose_bottom", "blocks"),
    # 牡丹：Java peony_* → 基岩 double_plant_paeonia_*（paeonia 不是 peony）
    "peony_top": ("double_plant_paeonia_top", "blocks"),
    "peony_bottom": ("double_plant_paeonia_bottom", "blocks"),
    # 大型蕨 / 高草（双格，基岩基色为 .tga）
    "large_fern_top": ("double_plant_fern_top", "blocks"),
    "large_fern_bottom": ("double_plant_fern_bottom", "blocks"),
    "tall_grass_top": ("double_plant_grass_top", "blocks"),
    "tall_grass_bottom": ("double_plant_grass_bottom", "blocks"),
    # 向日葵：Java front/top/back/bottom → 基岩 double_plant_sunflower_*
    "sunflower_front": ("double_plant_sunflower_front", "blocks"),
    "sunflower_top": ("double_plant_sunflower_top", "blocks"),
    "sunflower_back": ("double_plant_sunflower_back", "blocks"),
    "sunflower_bottom": ("double_plant_sunflower_bottom", "blocks"),
    # 矮草（单格）：Java short_grass → 基岩 tallgrass（注意与双格 tall_grass_* 不同）
    "short_grass": ("tallgrass", "blocks"),
    # 铁砧：Java 4 名 → 基岩 4 名（底座通用 + 按 damage 状态选顶面）
    #   anvil(底座/侧面)→anvil_base；anvil_top(完好)→anvil_top_damaged_0；
    #   chipped_anvil_top(微损)→anvil_top_damaged_1；damaged_anvil_top(重损)→anvil_top_damaged_2
    #   官方 bedrock-samples 四张 texture_set 齐全（16² 占位图），目标均可覆盖。
    "anvil": ("anvil_base", "blocks"),
    "anvil_top": ("anvil_top_damaged_0", "blocks"),
    "chipped_anvil_top": ("anvil_top_damaged_1", "blocks"),
    "damaged_anvil_top": ("anvil_top_damaged_2", "blocks"),
    # 丁香：Java lilac_* → 基岩 double_plant_syringa_*（syringa 是旧学名，基色为 .tga）
    "lilac_top": ("double_plant_syringa_top", "blocks"),
    "lilac_bottom": ("double_plant_syringa_bottom", "blocks"),
    # 盔甲：Java 分层 X_layer_1/2 → 基岩 X_1/2；皮革叫 cloth、锁链叫 chain
    "leather_layer_1": ("cloth_1", "models/armor"),
    "leather_layer_2": ("cloth_2", "models/armor"),
    "chainmail_layer_1": ("chain_1", "models/armor"),
    "chainmail_layer_2": ("chain_2", "models/armor"),
    "iron_layer_1": ("iron_1", "models/armor"),
    "iron_layer_2": ("iron_2", "models/armor"),
    "golden_layer_1": ("gold_1", "models/armor"),
    "golden_layer_2": ("gold_2", "models/armor"),
    "diamond_layer_1": ("diamond_1", "models/armor"),
    "diamond_layer_2": ("diamond_2", "models/armor"),
    "netherite_layer_1": ("netherite_1", "models/armor"),
    "netherite_layer_2": ("netherite_2", "models/armor"),
    "turtle_layer_1": ("turtle_1", "models/armor"),
    # ---- ENRO 实测补录（2026-11-19）----
    # 来源：用 ENRO 0.20.2 主体 128x.zip 跑转换，发现这些 Java 名未命中 484 表、
    # 同名直传会落空；逐条在 Mojang bedrock-samples v1.26.70.23-preview-full
    # 的 resource_pack/textures/blocks/ 实物中确认目标存在，且语义一一对应
    # （无"贴错材质"风险）。均属清单范围外的新增，非对既有映射的推翻。
    "cracked_stone_bricks": ("stonebrick_cracked", "blocks"),       # 裂纹石砖
    "mossy_stone_bricks": ("stonebrick_mossy", "blocks"),           # 苔藓石砖
    "dirt_path_side": ("grass_path_side", "blocks"),                # 泥土路径侧面（基岩旧名 grass_path）
    "dirt_path_top": ("grass_path_top", "blocks"),                  # 泥土路径顶面
    "flowering_azalea_leaves": ("azalea_leaves_flowers", "blocks"),  # 开花杜鹃叶
    "stonecutter_saw": ("stonecutter2_saw", "blocks"),              # 切石机锯片（tga）
    "nether_quartz_ore": ("quartz_ore", "blocks"),                  # 下界石英矿
    "tall_seagrass_bottom": ("seagrass_doubletall_bottom_a", "blocks"),  # 高海草底（tga）
    "tall_seagrass_top": ("seagrass_doubletall_top_a", "blocks"),        # 高海草顶（tga）
    # ---- 2026-11-20 补录：官方实物多面块（ENRO 源包都有，旧映射表缺）----
    # 三种炉的关态正面（_on 态此前已映射，_off 态缺）
    "blast_furnace_front": ("blast_furnace_front_off", "blocks"),
    "furnace_front": ("furnace_front_off", "blocks"),
    "smoker_front": ("smoker_front_off", "blocks"),
    # 新版本原木侧面（_top 此前已映射，_side 缺）
    "cherry_log": ("cherry_log_side", "blocks"),
    "mangrove_log": ("mangrove_log_side", "blocks"),
    "pale_oak_log": ("pale_oak_log_side", "blocks"),
    # 樱桃/红树/苍白橡木门（官方 blocks/ 根）
    "cherry_door_bottom": ("cherry_door_bottom", "blocks"),
    "cherry_door_top": ("cherry_door_top", "blocks"),
    "mangrove_door_bottom": ("mangrove_door_bottom", "blocks"),
    "mangrove_door_top": ("mangrove_door_top", "blocks"),
    "pale_oak_door_bottom": ("pale_oak_door_bottom", "blocks"),
    "pale_oak_door_top": ("pale_oak_door_top", "blocks"),
    # 工艺台顶面（ENRO 的 crafter_top_crafting → 基岩 crafter_top）
    "crafter_top_crafting": ("crafter_top", "blocks"),
    # 绯红/诡异门：官方在 blocks/huge_fungus/ 子目录，名为 *_lower/*_top
    "crimson_door_bottom": ("crimson_door_lower", "blocks/huge_fungus"),
    "crimson_door_top": ("crimson_door_top", "blocks/huge_fungus"),
    "warped_door_bottom": ("warped_door_lower", "blocks/huge_fungus"),
    "warped_door_top": ("warped_door_top", "blocks/huge_fungus"),
    # ---- 2026-11-20 第二轮：内容级核查发现的旧名/语义缺口 ----
    "quartz_pillar": ("quartz_block_lines", "blocks"),            # 石英柱 → 基岩旧名 lines
    "quartz_pillar_top": ("quartz_block_lines_top", "blocks"),    # 石英柱顶
    "sugar_cane": ("reeds", "blocks"),                            # 甘蔗 → 基岩旧名 reeds（tga）
    "terracotta": ("hardened_clay", "blocks"),                    # 陶瓦 → 基岩旧名 hardened_clay
    "cherry_leaves": ("cherry_leaves", "blocks"),                 # 樱花叶 → 基岩 tga（精确同名入表以触发 tga 输出）
}


def from_list(lst, pref):
    out = set()
    for l in lst:
        if l.startswith(pref + "/"):
            b = clean_base(l.split("/")[-1])
            if b:
                out.add(b)
    return out


def from_official(dirname):
    z = zipfile.ZipFile(OFFICIAL)
    pref = "resource_pack/textures/" + dirname + "/"
    suffix = ".texture_set.json"
    return set(n.split("/")[-1][:-len(suffix)] for n in z.namelist()
               if n.startswith(pref) and n.endswith(suffix))


JE, BE = lines(os.path.join(SRC, "texturesJE.js")), lines(os.path.join(SRC, "texturesBE.js"))

# 目标集合：官方样例包实物 ∪ 社区清单。按目录分开，避免跨目录误配。
CATS = {
    "blocks": (from_list(JE, "block"), from_list(BE, "blocks") | from_official("blocks")),
    "items":  (from_list(JE, "item"),  from_list(BE, "items")  | from_official("items")),
}

# ---------------- 词表 ----------------
COLORS_J = ["white", "orange", "magenta", "light_blue", "yellow", "lime", "pink",
            "gray", "light_gray", "cyan", "purple", "blue", "brown", "green", "red", "black"]
CMAP = {c: ("silver" if c == "light_gray" else c) for c in COLORS_J}

WOODS = {"oak": "oak", "spruce": "spruce", "birch": "birch", "jungle": "jungle",
         "acacia": "acacia", "dark_oak": "big_oak"}

# 颜色材质：Java 前缀式 → 基岩后缀式 / 旧基岩名
COLOR_PATTERNS = [
    ("{c}_wool", "wool_colored_{b}"),
    ("{c}_terracotta", "hardened_clay_stained_{b}"),
    ("{c}_glazed_terracotta", "glazed_terracotta_{b}"),
    ("{c}_concrete", "concrete_{b}"),
    ("{c}_concrete_powder", "concrete_powder_{b}"),
    ("{c}_stained_glass", "glass_{b}"),
    ("{c}_stained_glass_pane_top", "glass_pane_top_{b}"),
    ("{c}_shulker_box", "shulker_top_{b}"),
    ("{c}_candle", "candle_{b}"),
    ("{c}_candle_lit", "candle_{b}_lit"),
    ("{c}_stained_hardened_clay", "hardened_clay_stained_{b}"),
]

# 木材：Java 前缀式 → 基岩 log_/planks_/leaves_/sapling_ 前缀式
WOOD_PATTERNS = [
    ("{w}_planks", "planks_{b}"),
    ("{w}_log", "log_{b}"),
    ("{w}_log_top", "log_{b}_top"),
    ("{w}_leaves", "leaves_{b}"),
    ("{w}_sapling", "sapling_{b}"),
    ("stripped_{w}_log", "stripped_{b}_log"),
    ("stripped_{w}_log_top", "stripped_{b}_log_top"),
    ("{w}_door_bottom", "door_{w2}_lower"),
    ("{w}_door_top", "door_{w2}_upper"),
]

# 门：dark_oak 用原词；其余统一
DOOR_W = {"dark_oak": "dark_oak", "oak": "wood"}

# 花与植物的显式对照（逐条在目标集合中验证）
FLOWERS = {
    "allium": "flower_allium", "azure_bluet": "flower_houstonia",
    "blue_orchid": "flower_blue_orchid", "cornflower": "flower_cornflower",
    "dandelion": "flower_dandelion", "lily_of_the_valley": "flower_lily_of_the_valley",
    "oxeye_daisy": "flower_oxeye_daisy", "poppy": "flower_rose",
    "orange_tulip": "flower_tulip_orange", "pink_tulip": "flower_tulip_pink",
    "red_tulip": "flower_tulip_red", "white_tulip": "flower_tulip_white",
    "wither_rose": "flower_wither_rose",
}

# 其它已知差异（均在目标集合中验证后才收录）
MISC = {
    "grass_block_side": "grass_side", "grass_block_top": "grass_top",
    "grass_block_side_overlay": "grass_side_overlay",
    "andesite": "stone_andesite", "diorite": "stone_diorite", "granite": "stone_granite",
    "polished_andesite": "stone_andesite_smooth", "polished_diorite": "stone_diorite_smooth",
    "polished_granite": "stone_granite_smooth",
    "bricks": "brick", "stone_bricks": "stonebrick",
    "rail": "rail_normal", "activator_rail": "rail_activator",
    "detector_rail": "rail_detector", "powered_rail": "rail_golden",
    "attached_melon_stem": "melon_stem_connected", "melon_stem": "melon_stem_disconnected",
    "attached_pumpkin_stem": "pumpkin_stem_connected", "pumpkin_stem": "pumpkin_stem_disconnected",
    "bamboo_stalk": "bamboo_stem", "bamboo_large_leaves": "bamboo_large_leaf",
    "bamboo_small_leaves": "bamboo_small_leaf",
    "brown_mushroom": "mushroom_brown", "red_mushroom": "mushroom_red",
    "brown_mushroom_block": "mushroom_block_skin_brown",
    "red_mushroom_block": "mushroom_block_skin_red",
    "mushroom_stem": "mushroom_block_skin_stem",
    "carved_pumpkin": "pumpkin_face_off", "jack_o_lantern": "pumpkin_face_on",
    "beehive_end": "beehive_top", "beehive_front_honey": "beehive_front_honey",
    "chiseled_sandstone": "sandstone_normal", "chiseled_red_sandstone": "red_sandstone_normal",
    "cut_sandstone": "sandstone_smooth", "cut_red_sandstone": "red_sandstone_smooth",
    "cobweb": "web", "note_block": "noteblock", "spawner": "mob_spawner",
    "dead_bush": "deadbush", "tall_grass": "double_plant_grass_top",
    "sunflower": "double_plant_sunflower_top", "large_fern": "double_plant_fern_top",
    "lilac": "double_plant_syringa_top", "peony": "double_plant_paeonia_top",
    "rose_bush": "double_plant_rose_bottom",
}

# 语义存疑、拒绝纳入自动表的条目：目标名虽在权威集合里存在，但并非同一方块。
# 保留原名让用户在自定义映射里自行决定，避免把雕纹砂岩贴到普通砂岩上。
EXCLUDE = {
    "beehive_end", "chiseled_sandstone", "chiseled_red_sandstone",
}


def norm_tokens(s):
    """token 多重集归一化：仅用于「词序不同但用词完全一致」的安全自动推导"""
    s = s.lower().replace("light_gray", "silver")
    s = re.sub(r"stage(\d+)", r"stage_\1", s)
    return frozenset(t for t in s.split("_") if t)


def candidate_rules(j):
    """返回该 Java 基名的全部规则候选（不含验证）"""
    out = []
    for c in COLORS_J:
        b = CMAP[c]
        for src, dst in COLOR_PATTERNS:
            if j == src.format(c=c):
                out.append(dst.format(b=b))
    for w, b in WOODS.items():
        w2 = DOOR_W.get(w, w)
        for src, dst in WOOD_PATTERNS:
            if j == src.format(w=w, b=b, w2=w2):
                out.append(dst.format(b=b, w2=w2))
    # 生长阶段：stage0 → stage_0
    m = re.match(r"^(.*?)stage(\d+)$", j)
    if m:
        out.append(f"{m.group(1)}stage_{m.group(2)}")
    if j in FLOWERS:
        out.append(FLOWERS[j])
    if j in MISC:
        out.append(MISC[j])
    return out


def main():
    final, provenance, stats = {}, {}, collections.Counter()
    for cat, (J, T) in CATS.items():
        exact = J & T
        stats[f"{cat}:total"] = len(J)
        stats[f"{cat}:exact"] = len(exact)
        for j in sorted(J - T):
            if j in EXCLUDE:
                stats[f"{cat}:excluded"] += 1
                continue
            cands = [c for c in candidate_rules(j) if c in T]
            if not cands:
                stats[f"{cat}:unmapped"] += 1
                continue
            # 多候选时取第一个（规则按优先级排序），并记录
            pick = cands[0]
            if j in final and final[j] != pick:
                stats["conflict"] += 1
                continue          # 跨目录冲突：保留先写入的 blocks 版本
            final[j] = pick
            provenance[j] = "color" if j.startswith(tuple(c + "_" for c in COLORS_J)) else \
                            "wood" if any(j.startswith(w + "_") or j.startswith("stripped_" + w) for w in WOODS) else \
                            "flower" if j in FLOWERS else "misc"
            stats[f"{cat}:mapped"] += 1
            if len(cands) > 1:
                stats["multi_candidate"] += 1

    # ---- 补充通道：token 多重集完全一致、仅词序不同，且目标唯一 ----
    # 这是零歧义的推导（如 acacia_boat → boat_acacia），比相似度匹配安全得多。
    for cat, (J, T) in CATS.items():
        idx = collections.defaultdict(list)
        for t in T:
            idx[norm_tokens(t)].append(t)
        for j in sorted(J - T):
            if j in final or j in EXCLUDE:
                continue
            cands = idx.get(norm_tokens(j), [])
            if len(cands) == 1:
                final[j] = cands[0]
                provenance[j] = "auto-token"
                stats[f"{cat}:auto"] += 1
                stats[f"{cat}:mapped"] += 1
            elif len(cands) > 1:
                stats["auto_ambiguous"] += 1

    # 精确同名不入表；验证所有 value 都在目标集合
    # ---- 合并官方实物补录（MANUAL）：逐条断言目标在官方包实物中存在 ----
    with zipfile.ZipFile(OFFICIAL) as _z:
        _names = set(_z.namelist())

    def _exists(d, n):
        # d 可为 "blocks"、"blocks/<子目录>"（如 huge_fungus/deepslate）或 "models/armor"
        base = "resource_pack/textures/" + d
        if d == "models/armor":
            return f"{base}/{n}.png" in _names
        if d == "blocks" or d.startswith("blocks/"):
            return any(f"{base}/{n}{e}" in _names
                       for e in (".png", ".tga", ".jpg"))
        return False

    manual_ok = set()
    for _j, (_b, _d) in MANUAL.items():
        assert _exists(_d, _b), f"MANUAL 目标在官方实物中不存在: {_j} -> {_d}/{_b}"
        final[_j] = _b
        provenance[_j] = "manual-official"
        manual_ok.add(_b)
        stats["manual"] = stats.get("manual", 0) + 1

    T_all = set().union(*[t for _, t in CATS.values()])
    bad = {k: v for k, v in final.items() if v not in T_all and v not in manual_ok}
    assert not bad, f"有映射目标不在权威集合: {bad}"

    out = os.path.join(BASE, "name_map.json")
    json.dump(final, open(out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, sort_keys=True)

    print("=== 映射表生成结果 ===")
    for k in sorted(stats):
        print("  %-22s %5d" % (k, stats[k]))
    total_J = stats["blocks:total"] + stats["items:total"]
    covered = stats["blocks:exact"] + stats["items:exact"] + len(final)
    print("\n  映射表条目      : %d" % len(final))
    print("  总覆盖（精确+映射）: %d / %d (%.1f%%)" % (covered, total_J, 100 * covered / total_J))
    print("  输出: %s (%.1f KB)" % (out, os.path.getsize(out) / 1024))
    print("\n=== 分类构成 ===")
    print(" ", dict(collections.Counter(provenance.values())))
    print("\n=== 前 25 条 ===")
    for k in sorted(final)[:25]:
        print("  %-34s → %s" % (k, final[k]))

    # 未匹配清单（供文档附录）
    unresolved = {cat: sorted(J - T - set(final)) for cat, (J, T) in CATS.items()}
    json.dump(unresolved, open(os.path.join(SRC, "unresolved.json"), "w"),
              ensure_ascii=False, indent=1)
    meta = {
        "sources": {
            "java": "convertmcpack.net /pages/item_lists/texturesJE.js (Java 1.21.x)",
            "bedrock_web": "convertmcpack.net /pages/item_lists/texturesBE.js",
            "bedrock_official": "Mojang bedrock-samples v1.26.70.23-preview-full.zip texture_set.json",
        },
        "counts": dict(stats),
        "provenance": dict(collections.Counter(provenance.values())),
        "excluded_suspicious": sorted(EXCLUDE),
        "unresolved": unresolved,
    }
    json.dump(meta, open(os.path.join(SRC, "name_map_meta.json"), "w"),
              ensure_ascii=False, indent=1)
    print("\n=== 未匹配 ===")
    for cat, v in unresolved.items():
        print("  %-8s %d 个 → %s" % (cat, len(v), ", ".join(v[:12])))


if __name__ == "__main__":
    main()
