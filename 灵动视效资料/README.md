# 我的世界基岩版 · 灵动视效 / PBR 材质标准资料

> 整理日期：2026-11-16（2026-11-20 补 29 号）　|　共 24 份资料（7 份全文 + 2 份仅网址 + 15 份原创分析/设计）
> 本文件夹为**本地离线副本**；每个 `.md` 文件开头都标注了原始网址，请以原文为准。
> `_原始网页快照/` 保存了抓取成功页面的原始 HTML。

## 一句话理清关系

灵动视效（Vibrant Visuals）是基岩版的官方 PBR 图形模式，材质数据用 **MERS** 四通道存储：
R=金属度、G=自发光、B=粗糙度、A=次表面散射。
**LabPBR** 是 Java 版光影社区的另一套 `_s` / `_n` 纹理规范，通道语义不同，
因此两者之间需要转换（MineGraph 的 MERS 页末附有 LabPBR→MERS 转换工具）。
官方同时指出：MERS 的 `Alpha=0` 会正常生效，PNG 会被绘图工具优化掉 RGB 数据，
**推荐用 TGA 格式**（且实测为 32-bit BGRA、左下原点，PNG→TGA 需重排通道并翻转行序，见 `13_` 号）。

## 资料清单

| 序号 | 资料 | 本地文件 | 状态 |
|---|---|---|---|
| 01 | [LabPBR材质标准](https://docs.minegraph.cn/labpbrmaterialstandard.html) | [01_LabPBR材质标准.md](./01_LabPBR材质标准.md) | 全文已保存（4081 字） |
| 02 | [MERS材质标准](https://docs.minegraph.cn/mersmaterialstandard.html) | [02_MERS材质标准.md](./02_MERS材质标准.md) | 全文已保存（957 字） |
| 03 | [VibrantVisuals官方介绍](https://minecraft.net/zh-hant/vibrant-visuals-update) | [03_VibrantVisuals官方介绍.md](./03_VibrantVisuals官方介绍.md) | 全文已保存（4550 字） |
| 04 | [PBR概览](https://learn.microsoft.com/en-us/minecraft/creator/documents/rtxpbrintro?view=minecraft-bedrock-stable) | [04_PBR概览.md](./04_PBR概览.md) | 全文已保存（12382 字） |
| 05 | [TextureSet规范](https://learn.microsoft.com/en-us/minecraft/creator/reference/content/texturesetsreference/texturesetsconcepts/texturesetsintroduction?view=minecraft-bedrock-stable) | [05_TextureSet规范.md](./05_TextureSet规范.md) | 全文已保存（8591 字） |
| 06 | [灵动视效资源包](https://learn.microsoft.com/en-us/minecraft/creator/documents/vibrantvisuals/vvresourcepacks?view=minecraft-bedrock-stable) | [06_灵动视效资源包.md](./06_灵动视效资源包.md) | 全文已保存（3942 字） |
| 07 | [生物群系自定义](https://learn.microsoft.com/zh-tw/minecraft/creator/documents/vibrantvisuals/biomecustomization?view=minecraft-bedrock-experimental) | [07_生物群系自定义.md](./07_生物群系自定义.md) | 全文已保存（11334 字） |
| 08 | [中文 Minecraft Wiki · 灵动视效](https://zh.minecraft.wiki/w/Vibrant_Visuals?variant=zh-cn) | — | 仅保留网址 |
| 09 | [英文 Minecraft Wiki · Vibrant Visuals](https://minecraft.wiki/w/Vibrant_Visuals) | — | 仅保留网址 |
| 10 | **资源包结构分析**（原创整理，非抓取） | [10_灵动视效资源包结构分析.md](./10_灵动视效资源包结构分析.md) | 完整目录树 + schema + 引用链 + 版本演进 |
| 11 | **文件与文件夹命名全表**（原创整理，非抓取） | [11_文件与文件夹命名全表.md](./11_文件与文件夹命名全表.md) | 逐项命名 → 含义 / 功能 / 注意事项 |
| 12 | **官方样例包校验报告**（基于官方 ZIP 实物） | [12_官方样例包校验报告.md](./12_官方样例包校验报告.md) | 用 bedrock-samples v1.26.70.23-preview 逐项核对，修正 10/11 号的 8 处偏差 |
| 13 | **纹理文件通道与格式详解**（原创整理 + 像素级实测） | [13_纹理文件通道与格式详解.md](./13_纹理文件通道与格式详解.md) | 逐文件讲清 6 类贴图的通道 / 格式 / 命名 / 互斥，含 TGA 字节序、法线朝向与 `pbr/global.json` 回退 |
| 14 | **LabPBR → VV 安卓 App 设计**（产品化设计） | [14_LabPBR转VV安卓App设计.md](./14_LabPBR转VV安卓App设计.md) | 离线 APK 的用户流程 / 通道算法 / TGA 编码 / 名称映射 / Android 架构 / 测试 / 里程碑；**附录 A** 记录当时产出的路线 A 工程骨架（已按用户要求移除） |
| 15 | **Java → 基岩 纹理名映射表**（M3，可直接用） | [15_纹理名映射表.md](./15_纹理名映射表.md) | **478 条**映射（含 33 条官方实物补录）+ 六类命名规则 + 75.8% 覆盖率；产物 `LabPBR2VV/name_map.json` 已内置进网页版原型 |
| 16 | **端到端转换验证报告**（真实浏览器 + 官方包回归） | [16_端到端转换验证报告.md](./16_端到端转换验证报告.md) | 20 项静态 + Headless Chromium 完整转换 + 56 项逐文件校验 + 3,171 组官方 MERS 回归；记录并修复 2 个真 bug |
| 17 | **叠加报错根因与修复**（与 ENRO 等 PBR 包一起用报「资源包加载错误」） | [17_叠加报错根因与修复.md](./17_叠加报错根因与修复.md) | 实证定位 58 个 macOS `._` 伪 PNG + 全局单例 `pbr/global.json` 叠加冲突；产出叠加修复版 `.mcpack`、清洗工具、引擎 8 处补丁与「叠加模式」；订正前几轮的错误猜测 |
| 18 | **简介显示 / 多包叠加 / 光影扩展**（三问合辑） | [18_简介显示_多包叠加_光影扩展.md](./18_简介显示_多包叠加_光影扩展.md) | 游戏内简介三件套（manifest 描述 + `texts/` 本地化 + `pack_icon`）；多包叠加的顺序与 8 条不报错要求；VV 除贴图外可配置的光源/大气/体积雾/光轴/色彩分级/关键帧，及引擎级不可改项 |
| 19 | **除贴图外的可编辑项**（官方样例包实物） | [19_除贴图外的可编辑项.md](./19_除贴图外的可编辑项.md) | 从官方包实物提取 5 类配置 JSON 的真实字段 schema（大气/光照/色彩分级/水体/天空盒）+ 时间关键帧语法 + 群系绑定；配套可编辑模板在 `LabPBR2VV/vv_templates/` |
| 20 | **这些贴图为什么没转换成功**（成因实证与修复） | [20_未转换成功的成因与修复.md](./20_未转换成功的成因与修复.md) | 25 个文件逐项实测 + **用户真包 ENRO 0.20.2 二次实证**：名字关卡（paeonia/syringa/endframe/waterlily/farmland_dry…）、目录关卡（盔甲/地图被塞进 `blocks/`）、格式关卡（官方仅 `.tga` 的 50 项被 tga 压制）、地图不参与 PBR；**订正盔甲成因**——Java 1.21.2+ 改到 `entity/equipment/humanoid*`，被精确目录白名单误杀；产出目录修复 + 盔甲/床新路径映射 + TGA 名单 + 33 条映射补录 + 诊断脚本 |
| 21 | **Java 各版本的资源包目录与命名对应** | [21_Java各版本资源包目录与命名.md](./21_Java各版本资源包目录与命名.md) | 三个时代结构（`terrain.png` 贴图包 / `assets/minecraft` 资源包 / 1.13 扁平化）+ pack_format 1–88 全表 + Java↔基岩目录实测对照 + 六类命名规律 + 结构变更年表；转换器已内置 `pack_format` 代际识别 |
| 22 | **床与向日葵 UV 布局对比 + 床重 UV 实现**（两个真包逐像素） | [22_床与向日葵UV布局对比.md](./22_床与向日葵UV布局对比.md) | 向日葵 4 张逐像素 100% 一致（UV 可直接用）；床是同内容两套排布——Java 两块分离岛 vs 基岩单块连通岛，直接复制平均差 44.6；**已实现重 UV**（主岛删 48px 缝 + 顶部木条归位；床尾木架用基岩镂空规格 + Java 木纹，修复"腿缺透明"），16 色底部形状 IOU 1.0、全图差 2.75，基色/MERS/法线同步；附对比图、抽查实证与端到端验证；**§八 二次订正床腿"贴图拉伸"**——CCW 改转置映射 + 纵向填洞，底部差 23.15→15.54；**§九 三次订正"竖装拉伸"**——侧岛实为两个 96×96 单元，改【96×96 横向 tile】（sy=ty,sx=tx%96），碎块比例不变彻底无拉伸，底部差 15.54→14.48，附 `24_床腿竖拉伸_转置vs96tile修复.png` |
| 23 | **八类贴图"无法转换"的成因诊断**（两个真包逐像素实证） | [23_八类贴图无法转换的成因诊断.md](./23_八类贴图无法转换的成因诊断.md) | 草方块侧面/矮草/向日葵下半/高蕨/铁砧/切石机/诡异木板/绯红木板——10 组配对中 9 组内容 100% 同源，根因全是命名/目录差异（映射缺条目、目录层级不同、基岩无对应物），非转换器故障；逐类给出可否修复与所需改动；**§六 已落地修复**——补 `short_grass→tallgrass`、`sunflower_bottom→double_plant_sunflower_bottom` 两条映射（478→480），加 `DIR_REDIRECT` 把诡异/绯红木板输出到 `blocks/huge_fungus/` 并放行 blocks 子目录，4 组转换后逐像素 100% 一致，附 `25_矮草向日葵木板映射修复.png`；**§七 基于最新产物深层复查**——推翻单一"命名"归因，建立四层根因（L1 命名/目录·L2 格式优先级 .tga>.png·L3 texture_set 整份覆盖·L4 基岩无目标），证伪 `_mer` vs `_mers` 疑点（官方 3175 个全用 _mers），定位唯一确凿待修项=`tallgrass` 被官方 16² tga 占位压制（白名单漏录），附 `26_七类贴图四层根因分析.png`；**§七修复落地**——`TGA_BASE` 补 `tallgrass` 改写 128² tga，产物 `tallgrass.png→tallgrass.tga`，逐像素 100% 一致、全包仅此一处实质差异，备份 `ENRO_0.20.2_preTGAfix.mcpack`，至此 L1+L2 全部修复；**§八 基岩铁砧上材质机制 + 修复**——订正"铁砧 L4 无解"误判（原只搜网易包），官方 VV 有 4 张目标（anvil_base + anvil_top_damaged_0/1/2 + 状态选面），补 4 条映射（480→484），4 组逐像素 100% 一致，备份 `ENRO_0.20.2_preAnvilFix.mcpack`，附 `27_铁砧上材质机制与映射修复.png`；**§九 草侧面名字核实 + overlay 合成修复**——订正"作者重绘"误判（真因是 Java `_overlay` 未合成），官方基岩名确为 `grass_side.tga`，新增 `OVERLAY_SRC`/`OVERLAY_ONLY` 做 alpha 合成（合成后 vs 网易基岩图差 0.12、vs 理论图 100% 一致），冗余 overlay 文件消失（1399→1396），新增根因层 L5，备份 `ENRO_0.20.2_preGrassOverlayFix.mcpack`，附 `28_草侧面overlay合成修复前后.png` |
| 29 | **转换模块技术文档**（源码级归类，ConversionModule） | [29_转换模块技术文档.md](./29_转换模块技术文档.md) | 把网页里真正干转换的六类变换归成一个逻辑模块：重命名与路径映射 / 通道换算(LabPBR→MERS 公式) / 法线重建 / 床 UV 几何重构 / 格式编码(BGRA TGA) / 辅助变换+主流程编排；逐类给出输入输出、公式、行号、调用关系与维护坑；含 `ConversionModule` 命名空间（同一批函数的只读引用，功能零改动） |

> 第 10、11 份是基于官方资料重新整理的分析文档：10 号讲**结构**（manifest 门禁、texture_set 材质层、设置 JSON、`client_biome` 引用链、版本演进）；11 号讲**命名**（保留名、贴图后缀、注册表、踩坑清单）。
> 第 12 份是用 **Mojang 官方样例包实物**（`bedrock-samples-v1.26.70.23-preview-full.zip`，23,037 个文件）做的终审：主干结论均获印证，但修正了 8 处细节，包括 `default_fog_setting.json` 单复数、`textures_list.json` 非必需、四类目录原版包不存在、`format_version` 的正确含义。10/11 号文档已按报告加注修正。
> 第 13 份是专项深挖：针对 `textures/blocks/` 六类文件，把每个通道的定义、数值范围、图片格式、互斥规则与命名陷阱钉死，并直接解析官方 TGA/PNG 二进制验证字节序（BGRA）、位深（32/24-bit）与法线平面值 (128,128,255)。同时纠正了 11 号示意树容易被误读成「标准 6 件套」的问题。
> 第 14 份把上述结论**产品化**：设计一款离线安卓 App（上传 LabPBR 材质包 → 导出灵动视效 `.mcpack`），含用户流程、通道换算算法、TGA 编码、纹理名映射、Android 架构与三条落地路线、内存约束、测试与里程碑。**附录 A** 记录了当时产出的路线 A 工程骨架设计（该骨架已于 2026-11-15 按用户要求移除，14 号文档保留为设计史料）。**配套可运行原型见下方目录说明——网页版 `LabPBR2VV.html` 一直是、现在也是唯一可运行交付物**。
> 第 15 份是 **M3 名称映射表**：用官方样例包实物核对后发现 Java `block/` 只有 **56.5%** 与基岩精确同名，据此归纳六类规则生成 445 条映射（覆盖率 74.0%），并已内联进网页版原型。文档记录了三条被主动剔除的存疑映射——贴错材质比不映射更糟。
> 第 16 份是 **闭环验证**：用真实 Chromium 把「生成演示包 → 载入 → 转换 → 导出 `.mcpack`」完整跑通，再独立解包逐像素校验，最后拿官方 3,171 组 MERS 做 round-trip 回归。复核了 12/13 号结论、修正了 14 号一处近似值，并抓出修复了「演示包被 canvas 预乘 alpha 破坏」和「报告少算自身」两个真 bug。配套脚本在 `LabPBR2VV/verify/`，`bash verify/run_all.sh` 可一键复跑。
> 第 17 份是 **叠加报错根因实证**：用户把转换包与 ENRO 一起启用时报「资源包加载错误」。用两个包实物逐文件对照，定位到 58 个 macOS `._` AppleDouble 伪 PNG（非 PNG 内容却被当基色塞进 `textures/blocks/`）、两包都定义全局单例 `pbr/global.json` 的叠加冲突，以及空格文件名 / 重复 ZIP 条目。产出可直接叠加的修复版 `.mcpack`、清洗工具 `clean_pack.py`、引擎 8 处卫生补丁与「叠加模式」选项；并**订正了前几轮把 `format_version` 位置 / 封面当成根因的错误猜测**。
> 第 18 份是 **三问合辑**（外部检索整理，按来源可信度分层）：① 简介在游戏内怎么显示——`header.description`（纯文本、去 Java 色码）+ `texts/` 本地化（`.lang` 的 `pack.name`/`pack.description` + `languages.json`，换行用 `\n`）+ 128×128 `pack_icon.png` 封面；② 多包叠加——列表越上优先级越高、`texture_set.json` 不跨包合并（整组替换）、`pbr/global.json` 单例、包内卫生、能力/版本对齐等 8 条，与 17 号实证互相印证；③ VV 除贴图外还能配置光源、大气、体积雾、光轴、色彩分级、色调映射、群系与天气，多数支持按时间关键帧，但阴影/反射/平台配置等属引擎级改不了，制作可用 Bedrock Editor。**2026-11-16 追加**：第一节的「多语言简介」已落地到转换器——新增默认开启的开关，输出 `texts/` 三件套覆盖游戏内包名/简介，验证 +18 项全绿，详见 `18_` 号末尾「本次实现记录」。
> 第 20 份是**用户实测故障的归因闭环**：用户列出末地框架、绯红/诡异木板、全套盔甲、地图、耕地、睡莲、玫瑰、牡丹、高蕨、矮蕨、向日葵、丁香「没有转换成功」。用真实 Chromium 造包跑完整转换、再与官方包实物逐条比对，定位三类成因——① 命名错位（基岩用 `paeonia`/`syringa`/`endframe_*`/`waterlily`/`farmland_dry` 等另一套名字）；② 引擎目录推断 bug（`textures/models/armor/`、`textures/map/` 被兜底写进 `textures/blocks/`）；③ **扩展名优先级** `\.tga > .png`（Mojang Texture Sets 文档明文），官方仅用 `.tga` 的 50 个目标会把我们的 `.png` 静默压制——矮蕨/高蕨/丁香、以及此前认为"无需处理"的**树叶 `leaves_*` / `grass_side` 全在此列**。已修：目录沿用原路径 + PBR 白名单（地图/UI/字体显式跳过）、`TGA_BASE` 50 项按 tga 输出（alpha 未预乘、实测往返无损）、映射表 445→478（33 条逐条断言官方包存在）、新增诊断脚本 `verify/diag_unmapped.mjs`。同时**订正 `18_` 号"树叶不需要特殊处理"的说法**：PBR 通道层面成立，格式层面不成立。
> 第 22 份用用户两个真包（Java `ENRO 0.20.2 128x` / 基岩 `ENRO 0.20 网易版2`）**逐像素对比 UV**：向日葵 4 张 100% 一致、可无脑复制；床是"同内容两套排布"——Java 两块分离岛 vs 基岩单块连通岛，直接复制平均差 44.6，这是床"转了但观感不对"的真正根源（不是没生成文件）。附 `22_*.png` 对比图。**2026-11-16 追加**：① 抽查实证——306 组同名贴图 267 组（87.5%）逐像素一致，装备层 14 张全对齐，差异贴图二次归类为"UV 布局差异"与"内容/版本差异"；② **床重 UV 已落地**——转换器新增 `reuvBed()`（主岛删缝 + 顶部木条归位），基色/MERS/法线同步变换；③ **2026-11-16 再订正床腿**——实机反馈"腿缺透明"，查明旧版"侧岛转 90°"在底部是错的（Java 4 条 24px 细缝 vs 基岩 2 条 48px 宽腿，旋转无法互转，属 geometry UV 模型差异），改为「基岩镂空规格（公式化，16 色一致）+ Java 侧岛 CCW 木纹」合成，底部形状 IOU 0.60→**1.00**、全图差 5.38→**2.75**，修复床腿透明缝隙，详见 `22_` 号 §五 §六 §七。默认开启可关闭，真包端到端 CRC 全过。
> **2026-11-16 二次实证（真包）**：用户提供实际在用的 `ENRO 0.20.2 主体 128x`（38 MB / `pack_format 15` / 515 组 / 424 组法线）后复跑，订正了盔甲的成因——它不在 `textures/models/armor/`，而是 Java 1.21.2+ 新路径 `textures/entity/equipment/humanoid{,_leggings,_baby}/`，被「精确目录白名单」当成非 PBR 目录整批跳过。修复后同一份真包：成功转换 412 → **451 组**、输出 1282 → **1399 文件**、盔甲 0 → **69 文件**、床 0 → **48 文件**；剩余 21 组跳过为 painting/colormap/gui/map（基岩端不写 MERS）。详见 `20_` 号第六章。
> 第 21 份解决**版本维度**：Java 资源包结构变过两次——≤1.5.2 是 `terrain.png` 图集贴图包；1.6.1 起变成 `assets/minecraft/` + `pack.mcmeta`；1.13 扁平化把 `textures/blocks|items` 改成 `block|item` 并大改名。文档给出三时代结构树、`pack_format` 1–88 全表（含 1.21.11 之后改年份制、无 1.22）、Java↔基岩目录**实测**对照（基岩 `blocks/items` 复数、`ui` 对 `gui`、`models/armor` 同名但文件名为 `diamond_1`）、六类命名规律与结构变更年表。一个实用推论：**基岩保留了 Java 1.12 的旧命名**，所以 1.12 及更早的包直通率反而更高。转换器已内置 `pack_format` 识别，报告输出 `sourcePackFormat`/`sourceJavaVersion`/`sourceEra`。
> 第 19 份把第 18 份"光影扩展"那节的笼统结论**落到官方实物**：从 172MB 官方样例包里提取大气/光照/色彩分级/水体四类配置的真实字段（18+15+16+1 个实例）与时间关键帧语法、群系标识符绑定，并生成 `LabPBR2VV/vv_templates/` 可编辑模板（字段与官方逐一比对、无捏造）。天空盒因官方包无实例，只给接入说明不编造字段。
> 第 29 份是**源码级模块说明**：把网页转换器里真正干转换的六类变换（重命名/通道换算/法线重建/床 UV 重构/格式编码/辅助变换+编排）归成一个内聚的「转换模块 ConversionModule」，逐类给出输入输出、公式、最新行号、调用顺序与维护坑。它记录的是 2026-11-20 的一次**零功能改动**的结构归类：脚本里加总览 banner + `[转换模块·N]` 编号分区 + 末尾只读命名空间（同一批函数的引用，非第二份实现），已实测 `sameRef:true`、ENRO 515 组转换 0 失败。这份文档是理解/维护 `LabPBR2VV.html` 转换内核的入口。

## 仅保留网址的资料

以下站点有反爬保护，正文未能抓取，故只记录网址与内容摘要，需要时请自行打开：

- **08 中文 Minecraft Wiki · 灵动视效** — <https://zh.minecraft.wiki/w/Vibrant_Visuals?variant=zh-cn>
  - 中文术语、MERS 四通道定义、水面反射与焦散、光照反射、版本历史；最完整的中文百科条目（站点有反爬，未能保存全文）
- **09 英文 Minecraft Wiki · Vibrant Visuals** — <https://minecraft.wiki/w/Vibrant_Visuals>
  - RenderDragon 延迟光照管线、SSR/IBL 反射、Cook–Torrance 高光等技术细节（站点有反爬，未能保存全文）

## 目录结构

```
灵动视效资料/
├── README.md                       ← 本索引
├── 01_LabPBR材质标准.md            ← MineGraph 中文规范（Java 光影社区）
├── 02_MERS材质标准.md              ← MineGraph 中文规范（基岩版官方）
├── 03_VibrantVisuals官方介绍.md    ← Mojang 官方功能介绍
├── 04_PBR概览.md                  ← Microsoft Learn 创作者文档
├── 05_TextureSet规范.md            ← texture_set JSON 结构
├── 06_灵动视效资源包.md            ← manifest / capabilities / 目录结构
├── 07_生物群系自定义.md            ← 大气、光照、水体 JSON
├── 10_灵动视效资源包结构分析.md    ← 完整目录树与 schema 分析
├── 11_文件与文件夹命名全表.md      ← 逐项命名 / 含义 / 功能 / 注意事项
├── 12_官方样例包校验报告.md        ← 官方 ZIP 实物核对 + 8 处修正
├── 13_纹理文件通道与格式详解.md    ← 6 类贴图通道 / 格式 / 字节序 / 回退
├── 14_LabPBR转VV安卓App设计.md     ← 安卓 App 产品 / 架构 / 算法设计
├── 15_纹理名映射表.md              ← 478 条 Java→基岩映射 / 六类规则 / 覆盖率
├── 21_Java各版本资源包目录与命名.md ← 三时代结构 / pack_format 全表 / 目录对照
├── 16_端到端转换验证报告.md        ← 真实浏览器 / 逐文件校验 / 官方包回归 / 2 个 bug 修复
├── 17_叠加报错根因与修复.md        ← 与 ENRO 叠加报「加载错误」的实证根因 / 修复版包 / 叠加模式
├── 29_转换模块技术文档.md          ← 六类变换归类 / 公式 / 行号 / 调用链 / ConversionModule 命名空间
└── _原始网页快照/                  ← 原始 HTML 备份
```

> 配套产物（独立于本资料文件夹）—— **APK 工程已移除，以下仅列现存产物**：
> - **M0 网页原型** `/workspace/LabPBR2VV/LabPBR2VV.html` —— 单文件、零外部依赖，可上传 zip 完成真实转换并导出 `.mcpack`，一键生成演示包自测；**自动识别**贴图（`_s`/`_n` 配对）、目录归属、Java→基岩纹理名（478 条表）+ 源包 `pack_format` 代际识别、包名（`pack.mcmeta`/文件名）；游戏内封面为**输出侧统一生成**合规的唯一 `pack_icon.png`（128×128 正方形 PNG，支持自定义封面上传）；**扫描过滤 macOS `._` 垃圾 / 非法 PNG / 空格名、输出去重**，并新增「与现有 PBR 包叠加使用」选项（不输出全局单例 `pbr/global.json`）；**PNG 解码全程非预乘逐字节**（`alpha=0` 像素的 RGB 材质数据原样保留，见 `16_` 号补记二）；**Java `pack.mcmeta` 介绍同步到基岩 `header.description`**，并附转换时间/工具/选项记录（`_pbr2vv_report.json` 的 `conversion` 字段可追溯），详见 `16_`、`17_` 号文档。**2026-11-16 新增可视化预览**：扫描后点击表格任意一行，即可查看该组「原图 / `_s` 原样 / 转换后 MERS 四通道（R 金属、G 自发光、B 粗糙度、A 次表面 SSS）」与占比统计，`putImageData` 直写、不经 canvas 预乘，不影响材质数据。**2026-11-16 修复目录与格式两道关卡**：输出目录沿用 Java 原路径（`models/armor`、`map` 等不再被塞进 `blocks/`），非 PBR 目录（地图/UI/字体/画）显式跳过；命中官方「仅 tga」的 50 个目标时基色改写为 `.tga`，避免被官方 `.tga` 按 `tga>png>jpg` 优先级压制——详见 `20_` 号文档。
> - **叠加修复版成品** `/workspace/A Multi domain 1024x 叠加修复版.mcpack` —— 用户实测报错的转换包经清洗后的可直接叠加版（301 文件 / 142.2 MB，10 项复验全过）；清洗工具 `LabPBR2VV/verify/clean_pack.py` 可对任意转换包复跑，用法见 `17_` 号文档。
> - ~~**M2 安卓工程骨架**~~ **已移除**：`android/`（20 文件）与 `mapping/native_adapter.js`、`sync_assets.py` 已于 2026-11-15 按用户要求删除（沙箱无 Android SDK，从未编译出 APK）；设计史料见 14 号附录 A，恢复包在临时区 `apk_removed_backup.tar.gz`。项目现收敛为纯网页版形态。
> - **M3 映射表** `/workspace/LabPBR2VV/name_map.json` —— 478 条，已内联进网页版原型；生成脚本与清单在 `mapping/`，规则与覆盖率见 15 号文档。
> - **示例成品** `/workspace/LabPBR2VV/示例_LabPBR2VV.mcpack` —— 15 文件 / 10,203 B，可直接导入基岩版；由真实浏览器转换产出并通过 56 项逐文件校验。
> - **验证套件** `/workspace/LabPBR2VV/verify/` —— `run_all.sh` 一键复跑 5 步（静态 20 项 / CDP 端到端 / 包校验 56 项 / 官方 3,171 组回归），结构化结果在 `verify/out/*.json`；详见 16 号文档。

## 核心速查（MERS vs LabPBR）

| 通道 | MERS（灵动视效 / 官方） | LabPBR（Java 光影社区）`_s` |
|---|---|---|
| R 红 | 金属度 Metalness，0 非金属 → 255 金属 | 感知平滑度 Smoothness，255 完全光滑 |
| G 绿 | 自发光 Emissive，0 → 255 最大发光 | F0 基础反射率（0~229）/ 硬编码金属（230~255） |
| B 蓝 | 粗糙度 Roughness，0 光滑 → 255 粗糙 | 孔隙率（0~64）/ 次表面散射（65~255） |
| A 透明 | 次表面散射 Subsurface，0 → 255 | 自发光 Emissive，0~254（255 忽略） |

> 金属度与次表面散射互斥，游戏取两者较大值；相等时优先次表面散射。
> 法线纹理：LabPBR 的 `_n` 用 B 通道存材质 AO、A 通道存高度图，法线为 DirectX 格式（Y-）。
> 基岩侧法线同为 DirectX (Y-)，故 **LabPBR → VV 不需翻转 G 通道**，但需拆掉 B/A 里的 AO 与高度（依据为第三方转换器实现，详见 13 号第六节）。
