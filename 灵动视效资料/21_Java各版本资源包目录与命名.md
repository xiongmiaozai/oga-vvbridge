# 21 · Java 各版本的资源包目录与命名对应

> 整理日期：2026-11-16　|　场景：判断一个 Java 材质包属于哪一代结构、它的目录/文件名在新旧版本间怎么变、以及和基岩版怎么对应
> 来源：Minecraft Wiki（Resource pack / Pack format / 1.13 Resource pack changes）、Mojang `bedrock-samples` v1.26.70.23 实物清单、`resourcepackcreator`/`packsmc` 的 pack_format 表交叉核对
> 说明：`pack_format` 表以 Wiki 为准；标注「快照号」的中间值未全部收录（它们不对应正式版）。

---

## 一、三个时代：结构变过两次

### 时代 A · ≤1.5.2「贴图包」（Texture Pack）

没有 `assets/`，没有 `pack.mcmeta`：

```
<包名>.zip
├── terrain.png          ← 所有方块纹理拼在一张图集里
├── particles.png
├── gui/                 ← 界面
├── mob/                 ← 生物
├── armor/               ← 盔甲
├── item/                ← 物品
├── pack.png             ← 封面
└── pack.txt             ← 简介（纯文本，不是 JSON）
```

1.5（13w02a）起允许把 `terrain.png` 拆成 `textures/blocks/*.png` 单文件，但仍是老式包根结构。Mojang 官方给过两个转换工具：**Minecraft Unstitcher**（1.5 之前）、**TextureEnder**（1.5–1.6）。

### 时代 B · 1.6.1–1.12.2「资源包」诞生（pack_format 1–3）

一切搬进 `assets/minecraft/`，加了 `pack.mcmeta`：

```
<包名>.zip
├── pack.mcmeta                    ← {"pack":{"pack_format":1..3,"description":"..."}}
├── pack.png
└── assets/
    └── minecraft/
        ├── textures/
        │   ├── blocks/            ← 复数！方块
        │   ├── items/             ← 复数！物品
        │   ├── entity/
        │   ├── models/armor/      ← 盔甲（1.8 起 *_layer_1.png）
        │   ├── gui/
        │   ├── painting/
        │   ├── particle/
        │   ├── environment/
        │   ├── colormap/
        │   └── misc/
        ├── models/{block,item}/
        ├── blockstates/
        ├── lang/*.lang            ← 1.13 前是 .lang 纯文本
        └── sounds/
```

### 时代 C · 1.13+「扁平化」（pack_format 4+）

```diff
-        ├── textures/blocks/     ← 改名
+        ├── textures/block/      ← 单数
-        ├── textures/items/      ← 改名
+        ├── textures/item/       ← 单数
-        ├── lang/*.lang          ← 改为 JSON
+        ├── lang/*.json
```

后续又在 C 内部叠了四次目录级变化（见 §五）：

| 变化 | 版本 | 影响 |
|---|---|---|
| `atlases/` 目录 | 1.19.3 | 图集可配置 |
| `textures/gui/sprites/**` | 1.20.2 | GUI 从大图集拆成单文件 |
| 纹理只认 `.png` | 1.20.3 | `.tga`/`.jpg` 不再被读 |
| `items/` 物品模型定义 | 1.21.4 | 物品模型从 `models/item/` 迁出 |

> **1.13 是鸿沟**：`pack_format` 4 之前的包放到 1.13+，几乎每个方块/物品都会落错位置（黑白紫格子）。1.19.3 起 Mojang 甚至**移除了 format 3/4 的自动修正器**——老包不再被自动适配。

---

## 二、pack_format 全表（Java 正式版）

| format | 版本 | format | 版本 |
|---:|---|---:|---|
| 1 | 1.6.1–1.8.9 | 18 | 1.20.2 |
| 2 | 1.9–1.10.2 | 22 | 1.20.3–1.20.4 |
| 3 | 1.11–1.12.2 | 32 | 1.20.5–1.20.6 |
| 4 | 1.13–1.14.4 | 34 | 1.21–1.21.1 |
| 5 | 1.15–1.16.1 | 42 | 1.21.2–1.21.3 |
| 6 | 1.16.2–1.16.5 | 46 | 1.21.4 |
| 7 | 1.17–1.17.1 | 55 | 1.21.5 |
| 8 | 1.18–1.18.2 | 63 | 1.21.6 |
| 9 | 1.19–1.19.2 | 64 | 1.21.7–1.21.8 |
| 12 | 1.19.3 | 69 | 1.21.9–1.21.10 |
| 13 | 1.19.4 | 75 | 1.21.11 |
| 15 | 1.20–1.20.1 | 84 / 88 | 26.1 / 26.2 |

空缺的 10、11、14、16、17、19、20、21、24… 是只存在于快照的号，没有对应正式版。**1.21.11 之后不再有 1.22**，改用年份制（26.1、26.2），`pack_format` 也随之跳到 84/88。

---

## 三、Java ↔ 基岩 目录对照（基岩侧为官方包实测）

基岩 `resource_pack/textures/` 顶层实测（v1.26.70.23，文件数）：

```
blocks 3956 │ items 2662 │ entity 2555 │ ui 2046 │ gui 193 │ trims 171
particle 96 │ models 78 │ painting 66 │ environment 18 │ map 16
colormap 8 │ particles 6 │ misc 5 │ persona_thumbnails 4
```

| 用途 | Java | 基岩 | 对应关系 |
|---|---|---|---|
| 方块 | `textures/block/` | `textures/blocks/` | **单↔复数相反** |
| 物品 | `textures/item/` | `textures/items/` | **单↔复数相反** |
| 实体 | `textures/entity/` | `textures/entity/` | 同名 |
| 盔甲 | `textures/models/armor/` | `textures/models/armor/` | 同名，**但文件名不同**（`diamond_layer_1` → `diamond_1`） |
| 画 | `textures/painting/` | `textures/painting/` | 同名 |
| 地图 | `textures/map/` | `textures/map/` | 同名；基岩侧**无 texture_set，不参与 PBR** |
| 粒子 | `textures/particle/` | `textures/particle/`（另有历史 `particles/`） | 同名 |
| 界面 | `textures/gui/`（1.20.2 起 `gui/sprites/**`） | `textures/ui/` + 少量 `textures/gui/` | **目录不同名**，且布局逻辑完全不同 |
| 群系着色 | `textures/colormap/` | `textures/colormap/` | 同名 |
| 环境 | `textures/environment/` | `textures/environment/` | 同名（日月、云、雨雪） |
| 杂项 | `textures/misc/` | `textures/misc/` | 同名 |
| 盔甲纹饰 | `textures/trims/` | `textures/trims/` | 同名（171 个） |
| 附魔光效 | `textures/misc/enchanted_glint_*.png`（1.19.4 拆分） | `textures/misc/enchanted_item_glint.png` | 文件名不同 |
| 状态效果图标 | `textures/mob_effect/` | 并入 `textures/ui/` | 结构合并 |
| 界面遮罩/暗角 | `textures/misc/vignette.png` | `textures/ui/` 或引擎内置 | 不通用 |
| 音效 | `assets/minecraft/sounds/` | `assets/sounds/`（无 `minecraft/`） | 层级不同 |
| 语言 | `lang/*.json`（键值 JSON） | `texts/*.lang` + `texts/languages.json` | 格式不同 |

---

## 四、命名对应的六类规律

### 1) 木材类：前缀 ↔ 后缀换位

```
Java oak_planks        → 基岩 planks_oak
Java dark_oak_log      → 基岩 log_big_oak      （dark_oak 在基岩叫 big_oak）
Java spruce_leaves     → 基岩 leaves_spruce
```

### 2) 颜色类：颜色位置不同

```
Java white_wool              → 基岩 wool_colored_white
Java light_gray_concrete     → 基岩 concrete_silver   （gray→silver）
Java black_terracotta        → 基岩 hardened_clay_stained_black
```

### 3) 分类前缀：基岩爱加类别词

```
Java poppy        → 基岩 flower_rose
Java dandelion    → 基岩 flower_dandelion
Java allium       → 基岩 flower_allium
Java cobweb       → 基岩 web
Java spawner      → 基岩 mob_spawner
```

### 4) 双格植物：Java 用 top/bottom，基岩用 double_plant_

```
Java large_fern_top      → 基岩 double_plant_fern_top
Java tall_grass_bottom   → 基岩 double_plant_grass_bottom
Java lilac_top           → 基岩 double_plant_syringa_top   （lilac→syringa）
Java peony_bottom        → 基岩 double_plant_paeonia_bottom（peony→paeonia）
Java sunflower_front     → 基岩 double_plant_sunflower_front
```

### 5) 基岩保留 1.12 旧名（关键规律）

基岩没有经历 Java 1.13 的扁平化改名，**很多旧名一直用到现在**：

| 语义 | Java 1.13+ | 基岩（= Java 1.12 名） |
|---|---|---|
| 草方块侧面 | `grass_block_side` | `grass_side` |
| 花岗岩 | `granite` | `stone_granite` |
| 圆石 | `cobblestone` | `cobblestone`（同名） |
| 橡木木板 | `oak_planks` | `planks_oak` |
| 砖块 | `bricks` | `brick` |
| 西瓜 | `melon` | `melon_block` |

> **推论**：Java **1.12 及更早**的材质包，文件名反而和基岩更接近——很多条目直接同名可用，映射需求比 1.13+ 的包少得多。这是老包转换时的一个天然优势。

### 6) 语义化重命名（仅 Java 侧发生）

```
1.13  grass → grass_block        plank/planks → oak_planks 等
1.13  log → oak_log              bark → wood
1.13  melon_block → melon        portal → nether_portal
1.13  xp_orb → experience_orb    mob_spawner → spawner
1.17  grass_path → dirt_path
1.20.3 grass（方块/物品）→ short_grass
```

---

## 五、结构性变更年表

| 版本 | format | 结构/命名变化 |
|---|---:|---|
| 1.6.1 (13w24a) | 1 | 贴图包 → 资源包；`assets/minecraft/`；`pack.mcmeta`；`pack.txt`→JSON 描述 |
| 1.9 (15w31a) | 2 | 模型系统重写（multipart、物品标签谓词） |
| 1.11 (16w32a) | 3 | **所有文件名强制小写** |
| 1.13 (17w48a) | 4 | **扁平化**：`blocks→block`、`items→item`；`lang` 改 JSON；方块/物品 ID 大改名 |
| 1.14 | 4 | 纹理更新（美术替换，不改路径）；内置 `Programmer Art` 旧纹理包 |
| 1.15 (pre1) | 5 | 箱子/旗帜/盾牌图案改用 **alpha 通道** |
| 1.16.2 (rc1) | 6 | 墙的模型/贴图变更（MC-197275） |
| 1.17 (20w45a) | 7 | `grass_path → dirt_path`；溺尸纹理镜像方式变化 |
| 1.18 (21w39a) | 8 | `inventory.png` 增加薄版效果列表 sprite |
| 1.19 (22w11a) | 9 | `pack.mcmeta` 支持 `filter` |
| 1.19.3 | 12 | **新增 `atlases/`**；**移除 format 3/4 的自动修正器**（1.12 老包不再被适配）；纹理先于模型加载 |
| 1.19.4 | 13 | 附魔光效拆成 `enchanted_glint_entity/item.png`；`legacy_smithing.png` |
| 1.20–1.20.1 | 15 | 字体更新（Unifont 15）；`credits.json` 分级 |
| 1.20.2 | 18 | **GUI 拆成 `textures/gui/sprites/**`**；`supported_formats`；`overlays/` |
| 1.20.3–1.20.4 | 22 | **纹理只支持 `.png`**；`grass → short_grass`；蝙蝠模型改 |
| 1.20.5–1.20.6 | 32 | 物品组件化；`map_icons.png` 拆到 `textures/map/decorations/` |
| 1.21.4 | 46 | 物品模型定义迁到 `items/` |
| 1.21.9–1.21.10 | 69 | `min_format`/`max_format` 取代 `supported_formats` |
| 1.21.11 → 26.2 | 75 / 84 / 88 | 版本号改年份制，无 1.22 |

---

## 六、对转换器的意义（已落地）

### 1) 旧包在目录层面本来就通

扫描器只要求路径含 `textures/`，因此 `textures/blocks/`（旧）和 `textures/block/`（新）都能被扫到；目录名也会被原样保留。**真正需要的是"老文件名"，而不是"老目录"**。

### 2) `pack_format` 自动识别（本次新增）

读 `pack.mcmeta` 的 `pack.pack_format`，映射到具体版本与代际，显示在扫描结果并写入报告：

| 字段 | 含义 |
|---|---|
| `conversion.sourcePackFormat` | 源包声明的 `pack_format` |
| `conversion.sourceJavaVersion` | 对应 Java 版本区间，如 `1.20–1.20.1` |
| `conversion.sourceEra` | `pre-1.13` / `1.13-1.14` / `1.15+`，决定目录与命名体系 |

扫描结果会显示 `Java 1.20–1.20.1（pack_format 15）`；若判定为 `pre-1.13`，额外提示「旧名多为基岩现名，通常直通」。

### 3) 三条实操结论

- **1.12 及更早的包**：命中映射的机会少、直通的机会多；如果发现大量"未映射但名字对得上"，是正常的，不是失败。
- **1.20.3+ 的包**：源纹理一定只有 `.png`（Mojang 已不再读 `.tga/.jpg`），但不影响基岩输出——基岩侧仍需要按 `tga>png>jpg` 的优先级决定输出格式（见 `20_` 号）。
- **1.19.3+ 的游戏**：即使把 1.12 老包直接丢进 Java 版，也不再自动适配；但本工具是**转成基岩包**，不受这条限制，只需担心名字对不上。

---

## 七、验证

| 项目 | 结果 |
|---|---|
| 静态守卫 | **44/44**（新增 E 组：`JAVA_PACK_FORMATS`/`javaVersionOf`/`javaEraOf`/报告字段） |
| 端到端 | 通过（新增断言：demo 包 `pack_format=15` → 报告 `15/1.15+`） |
| 包校验 | 72/72 |
| 官方回归 | 3171 / 3171 |
| 清洗自测 | 9/9 |

---

## 八、未覆盖

- **快照号**（10/11/14/16/17/19/20/21/24/70.1/71–74/76–81…）未收录，遇到时报告会显示"未收录的快照号"，代际仍按数值区间推断。
- **1.5 之前**的 `terrain.png` 图集包：本工具不解析图集切分，无法转换（需要先用 TextureEnder/Unstitcher 还原成单文件）。
- **1.13 的完整逐文件改名表**：Wiki 该页面的表格是折叠组件，抓取只能拿到标题，未能取得全量清单；本文只列了结构性规律与高频样例。若需要逐条核对，可直接读目标版本的 `client.jar` 内 `assets/minecraft/textures/` 实际文件名。
