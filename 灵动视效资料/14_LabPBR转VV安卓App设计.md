# LabPBR → 灵动视效（VV）安卓 App 设计

> 代号：**PBR2VV**　|　设计日期：2026-11-15
> 定位：一款**纯离线**的 Android 应用，玩家选择 Java 版 LabPBR 材质包（zip），一键产出可导入基岩版的 `.mcpack`（Vibrant Visuals PBR 资源包）
> 依据：本地 `01`–`13` 号资料，其中 `12` 号为 Mojang 官方样例包实物校验、`13` 号为通道与格式的像素级实测
> 配套可运行原型：`/workspace/LabPBR2VV/LabPBR2VV.html`（单文件，含完整转换引擎与演示包生成）

---

## 一、产品定义

### 1.1 做什么

| 项 | 内容 |
|---|---|
| 输入 | Java 版资源包 `.zip`：含 `pack.mcmeta` + `assets/<ns>/textures/**/*.png` 及其 `_s` / `_n`  companion |
| 输出 | 基岩版 `.mcpack`：`manifest.json` + `textures/{blocks,items,entity}/<name>.png` + `<name>.texture_set.json` + `<name>_mers.tga` + 可选 normal + 转换报告 |
| 运行环境 | Android 8.0+，**全程本地**，无网络、无账号、无上传 |
| 核心壁垒 | 把 **LabPBR 与 MERS 的通道语义差异**正确自动化（现成工具普遍算错，见 §5.9） |

### 1.2 明确不做

- ❌ 不做 Java → 基岩的**全量**资源包转换（模型 / blockstates / 声音 / 语言文件），只转 PBR 材质层
- ❌ 不内置 Mojang 原版贴图（版权），也不联网下载任何材质
- ❌ 不做 RTX 包（`_mer.png`）—— 目标只有 Vibrant Visuals
- ❌ 不做光影/着色器，不修改游戏本体
- ❌ 不生成 `textures_list.json`（官方样例包实测非必需，`12_` 号报告）

### 1.3 为什么这个 App 值得做

`13_` 号文档证明官方原版包的材质层是**严格三件套**（`.png` + `.texture_set.json` + `_mers.tga`，3,171 组 1:1），而 Java 侧是 `.png` + `_s.png` + `_n.png`。两者通道语义完全不同，手工转换必然出错；`G2F1SH/Lab2MERS` 这类现成工具又存在三处硬伤。App 的价值就是把这套**已验证的映射规则 + TGA 编码 + 打包**封装成一次点击。

---

## 二、用户流程（5 步）

```
① 选包 ──→ ② 扫描 ──→ ③ 配置 ──→ ④ 转换 ──→ ⑤ 导出
 SAF 选 zip   识别/配对    策略选项    逐张处理     .mcpack + 报告
              + 映射预览              进度/日志    分享/保存到设备
```

| 步骤 | UI 要点 | 失败处理 |
|---|---|---|
| ① 选包 | 大号拖放区 + 「选择 .zip」；支持「生成演示包」自测 | 非 zip / 无 `pack.mcmeta` → 提示「未识别为 Java 资源包」，仍允许强制继续 |
| ② 扫描 | 统计卡：基色 N 张 / `_s` N 张 / `_n` N 张 / 命名空间数 / 未映射数；表格预览「原名 → 目标名 → 状态」 | 0 张 `_s` → 提示「可能不是 LabPBR 包」，提供「为全部基色生成默认 MERS」选项 |
| ③ 配置 | 包名、目标引擎版本、金属度策略、粗糙度曲线、是否输出 normal / SSS / AO 烘焙、命名映射策略 | 参数非法即时校验 |
| ④ 转换 | 逐张进度条 + 可展开日志；可暂停 / 取消 | 单张失败不中断整批，记入报告 |
| ⑤ 导出 | 「保存 .mcpack」「分享」「查看报告」；展示输出文件数、体积、警告数 | 保存失败走系统分享面板兜底 |

设计原则：**扫描结果必须先给用户看，再开始转换**——纹理名映射是唯一无法 100% 自动化的环节，需要让用户有机会导出映射表人工修正。

---

## 三、输入规范（Java / LabPBR 资源包）

```
<input>.zip
├── pack.mcmeta                        pack_format / supported_formats
├── pack.png                           可选
└── assets/<namespace>/textures/
    ├── block/<name>.png               基色（必需）
    ├── block/<name>_s.png             反射/高光纹理（LabPBR，本 App 的输入核心）
    ├── block/<name>_n.png             法线 + AO + 高度（可选）
    ├── block/<name>.png.mcmeta        动画帧元数据（可选，需保留帧布局）
    └── item/ , entity/ , ...
```

**配对规则**：同目录、同基名，`<name>.png` ↔ `<name>_s.png` ↔ `<name>_n.png`。区分大小写。

**LabPBR `_s` 通道**（`01_` 号文档第 20–79 行，原文公式）：

| 通道 | 含义 | 取值 |
|---|---|---|
| R | **感知平滑度** | 0 粗糙 → 255 完全光滑；`粗糙度 = pow(1 − 感知平滑度, 2)` |
| G | **F0 / 硬编码金属** | 0–229 = F0（线性，229≈90%）；230–255 = 预定义金属，**该区间一律视作金属** |
| B | **孔隙率 / SSS** | 0–64 = 孔隙率；65–255 = 次表面散射；金属/导体该通道「暂留」 |
| A | **自发光** | 0–254 线性；**255 = 忽略** |

**LabPBR `_n` 通道**（`01_` 号文档第 113–132 行）：

| 通道 | 含义 |
|---|---|
| R / G | 切线空间法线 X / Y，**DirectX 格式（Y−）**：X 轴向右、Y 轴向下 |
| B | 材质 AO（0 = 100% 遮蔽，255 = 无遮蔽） |
| A | POM 高度图（0 = 25% 深度，建议 ≥1） |

法线 Z 由 `z = sqrt(1.0 − dot(normal.xy, normal.xy))` 重建 —— 因为 B 被 AO 占用了。

**硬编码金属表**（`01_` 号文档第 89–98 行，G 值）：铁 230 / 金 231 / 铝 232 / 铬 233 / 铜 234 / 铅 235 / 铂 236 / 银 237；255 = 用反照率当 F0（不精确但可用）。

**旧格式辨识**（必须做，否则会静默算错）：SEUS PBR / Old PBR 的法线是 **OpenGL (Y+)** 且 specular 是 RGB=Rough/Metal/Emissive。检测到这类布局应弹窗要求用户确认，或按 `flip_normal_y` 处理。可引用 `flodri/RGBA-Formats-Converter` 的判别逻辑。

---

## 四、输出规范（VV `.mcpack`）

```
<包名>.mcpack                          （就是 ZIP，manifest 必须在根，不套外层目录）
├── manifest.json
├── pack_icon.png
├── textures/
│   ├── blocks/
│   │   ├── <mapped>.png               基色，原样复制
│   │   ├── <mapped>.texture_set.json
│   │   └── <mapped>_mers.tga          32-bit BGRA
│   │   └── <mapped>_normal.tga        可选
│   ├── items/ , entity/ , particle/
└── _pbr2vv_report.json                转换报告（可选，游戏忽略）
```

**`manifest.json`**（第三方包必须带 `capabilities`，不能照抄官方样例包 —— `12_` 号报告最重要的一条）：

```json
{
  "format_version": 2,
  "header": {
    "name": "<用户填的包名>",
    "description": "Converted from LabPBR by PBR2VV",
    "uuid": "<每次生成随机 UUID v4>",
    "version": [1, 0, 0],
    "min_engine_version": [1, 21, 120]
  },
  "modules": [
    { "type": "resources", "uuid": "<另一个 UUID v4>", "version": [1, 0, 0] }
  ],
  "capabilities": ["pbr"]
}
```

**`*.texture_set.json`**（`13_` 号文档第三节、`05_` 号文档）：

```json
{
  "format_version": "1.21.30",
  "minecraft:texture_set": {
    "color": "<mapped>",
    "metalness_emissive_roughness_subsurface": "<mapped>_mers"
  }
}
```

> 硬约束：值**不带扩展名**；MER ⊕ MERS、normal ⊕ heightmap 互斥；`color` 必填；引用贴图必须在同一包内。违反任一条件 → `CONTENT_ERROR`，整个纹理集失效。

**`_mers.tga`**：32-bit **BGRA**、左下原点、8 alpha bits（`13_` 号文档第 5.3 节像素级实测）。PNG 改后缀无效，必须重排通道 + 翻转行序。

---

## 五、核心算法（本 App 的技术核心）

### 5.1 通道映射总表

| 源（LabPBR `_s`） | → 目标（MERS） | 公式 | 边界 / 说明 |
|---|---|---|---|
| R 感知平滑度 `s` | **B 粗糙度** | `B = round(255 · pow(1 − s/255, 2))` | 01 号文档原文公式；**不能线性反转** |
| G F0 / 金属 `g` | **R 金属度** | `g ≥ 230 ? 255 : 0`（默认策略） | F0 0–229 是介电质反射率，**VV 无对应通道，信息不可逆丢失** |
| A 自发光 `a` | **G 自发光** | `a = 255 ? 0 : round(a · 255/254)` | 255 是 LabPBR 保留值（不透明），必须忽略 |
| B SSS / 孔隙率 `b` | **A 次表面散射** | `b ≥ 65 ? round((b−65) · 255/190) : 0` | `b ≤ 64` 是孔隙率，VV 无对应 → 丢弃 |
| — | **金属与 SSS 互斥** | `if (R > A) A = 0` | 引擎取 `max(metalness, subsurface)`，相等优先 SSS（`05_`/`02_` 号） |

### 5.2 三种金属度策略（用户可选）

| 策略 | 行为 | 适用 |
|---|---|---|
| **二值（默认，推荐）** | `g≥230 → 255`，否则 `0` | 符合 MS Learn「建议金属度当二值用」 |
| 保留 F0 为部分金属（实验） | `g<230 → round(g/229·255)` | 不物理准确，仅特殊风格；默认关闭并在报告里警告 |
| 全部非金属 | 强制 `R=0` | 只想借用发光/粗糙度时 |

> ⚠️ 无论哪种策略，都要在报告里明确列出「有多少像素的 F0 / 孔隙率信息被丢弃」——这是 LabPBR → MERS 的固有损失，不能假装没发生。

### 5.3 `_n` 拆解（可选功能）

```text
X = R/255·2 − 1
Y = G/255·2 − 1              // DirectX Y−，与 VV 同向，不翻转 G（13_ 号 §6.3）
Z = sqrt(max(0, 1 − X² − Y²))   // 01_ 号文档原文公式
normal RGB = (R, G, (Z·0.5+0.5)·255)
AO        = 原 B   → 可烘焙进基色（乘算）或丢弃
高度      = 原 A   → 可输出 _heightmap.tga（默认关）
```

默认**不输出** normal / heightmap：官方样例包 3,171 个纹理集里只有 4 个用 normal、0 个用 heightmap，且 VV 中 item 禁用 heightmap（`12_`/`13_` 号）。开启时需在 UI 提示这一限制。

### 5.4 参考实现（JS，与配套原型同源）

```javascript
function labpbrToMers(r, g, b, a, opt = {}) {
  const s = r / 255;
  let rough = Math.pow(1 - s, 2);                    // → MERS.B
  let metal = (g >= 230) ? 1 : 0;                   // → MERS.R
  if (opt.metalPolicy === 'f0') metal = g / 229;     // 实验策略
  if (opt.metalPolicy === 'none') metal = 0;
  let emis = (a === 255) ? 0 : (a / 254);           // → MERS.G
  let sss  = (b >= 65) ? (b - 65) / 190 : 0;        // → MERS.A
  if (metal > sss) sss = 0;                         // 金属与 SSS 互斥：取大值，相等时优先 SSS
  else if (sss > metal) metal = 0;
  return [metal, emis, rough, sss].map(v => Math.round(v * 255));
}
```

> ⚠️ **输入端解码的隐藏坑（M0 原型实测踩到）**：LabPBR 的 `_s` 用 **alpha 通道存自发光**，大量像素 `alpha=0`。若用浏览器 `canvas.getImageData()` 或任何**预乘 alpha** 的解码路径，`alpha=0` 区域的 RGB 会被抹成 0 —— 即 R 平滑度 / G F0 / B SSS 三个材质通道全部丢失，而且**静默出错、不报异常**。原型因此自实现了 PNG 解码器（直接解 `IHDR` + `IDAT` + unfilter，拿原始字节，零信息损失）。Android 原生侧同理：需确认 `Bitmap` 的 premultiplied 设置，或走字节级解码。这与 `13_` 号文档「MERS 输出必须用 TGA」是**同一个坑在输入端与输出端的两次出现**，是本 App 最容易被测漏的缺陷。

### 5.5 TGA 编码器

```javascript
function encodeTGA(w, h, rgba /* RGBA, 左上原点 */) {
  const buf = new Uint8Array(18 + w * h * 4), dv = new DataView(buf.buffer);
  buf[2] = 2;                       // uncompressed true-color
  dv.setUint16(12, w, true); dv.setUint16(14, h, true);
  buf[16] = 32; buf[17] = 8;        // 32-bit, 8 alpha bits, 左下原点
  let p = 18;
  for (let y = h - 1; y >= 0; --y) for (let x = 0; x < w; ++x) {
    const i = (y * w + x) * 4;
    buf[p++] = rgba[i + 2];        // B
    buf[p++] = rgba[i + 1];        // G
    buf[p++] = rgba[i];            // R
    buf[p++] = rgba[i + 3];        // A
  }
  return buf;
}
```

自检：写出后读回文件头，应满足 `depth=32 / alpha_bits=8 / y_top=0`；拿官方 `iron_block_mers.tga` 反解应得 `R≈191, G=0, B≈137, A=0`（`13_` 号 §5.3）。

### 5.6 与现成工具的错误对照（`G2F1SH/Lab2MERS.py`）

| 输出通道 | 它的做法 | 本 App 修正 |
|---|---|---|
| R 金属度 | `new_r = g`，直接搬 F0 | F0 0–229 是介电质反射率，不是金属度；只有 `g≥230` 才是金属 |
| B 粗糙度 | `255 − r` **线性反转** | `pow(1−s, 2)`，**漏了平方** |
| G 自发光 | `new_g = a` | 需处理 255 保留值，且 254→255 归一 |
| A SSS | `b≥65` 线性映射 | 基本一致，但需补金属互斥 |
| `_n` | **完全不处理** | 需拆 AO / 高度 / 重建 Z |
| 输出格式 | `--format` 默认 **png** | **必须 TGA**（Alpha=0 有意义） |
| 配套文件 | 不生成 | 必须生成 `texture_set.json` + `manifest.json` |

### 5.7 纹理名映射（工程量最大的一块）

| Java 路径 | 基岩路径 | 说明 |
|---|---|---|
| `assets/minecraft/textures/block/` | `textures/blocks/` | 单复数差异 |
| `assets/minecraft/textures/item/` | `textures/items/` | 同上 |
| `assets/minecraft/textures/entity/` | `textures/entity/` | 一致 |
| `assets/<mod_ns>/textures/...` | `textures/blocks/` | 自定义命名空间：保留原名，报告标记 |

多数方块名在 1.13 扁平化后与基岩同名，但存在一批不一致（玻璃、混凝土、木材、矿石等）。策略：

1. 内置一份**可维护的映射表 JSON**（首版 100–300 条，参考 `Seraphic-Studio/JE2BE-Resource-Pack-Converter` 的现成映射）；
2. 未命中 → **保留原名**并在报告里列出，用户可导出映射表编辑后回导；
3. 同名冲突 → 按命名空间加前缀，避免覆盖；
4. 动画纹理 `.png.mcmeta` → 保持帧图纵向排列，不重排像素。

### 5.8 缺省值回退

若某基色**没有** `_s`：不凭空造贴图，按 `13_` 号第八节写 `pbr/global.json`（`minecraft:pbr_fallback_settings`，`format_version: "1.21.40"`，`blocks`/`actors`/`particles`/`items` 四类 `global_metalness_emissive_roughness_subsurface`）。用户也可选择「为无 `_s` 的贴图生成均匀 MERS 贴图」。

---

## 六、Android 架构

### 6.1 三条落地路线

| 路线 | 做法 | 工期 | 优点 | 缺点 | 建议 |
|---|---|---|---|---|---|
| **A. WebView 壳** | Kotlin 单 Activity + `WebViewAssetLoader`，内嵌本设计的 HTML/JS 引擎；原生只负责 SAF 选文件与导出 | 最短 | 一套代码同时是网页版；算法与原型同源 | 图像处理走 JS canvas，超大包内存吃紧 | ✅ **首版推荐** |
| **B. Capacitor** | 把 Web 工程用 Capacitor 包成 Android 工程，文件能力用 `@capacitor/filesystem` + file-picker 插件 | 短 | MIT 免费、插件生态全、易上架 | 多一层依赖；仍需处理 Scoped Storage | ✅ 需要上架时用 |
| **C. 原生 Kotlin** | `BitmapFactory` + 自写 TGA 编码 + `ZipOutputStream` | 长 | 性能/内存最好，可后台 Service | 算法要重写一遍，与原型不同源 | 二期再做 |

> 推荐路径：**A 做 MVP → B 上架 → C 处理 512× 以上大包**。配套原型 `LabPBR2VV.html` 就是路线 A 的 Web 层，可直接放进 `assets/`。

### 6.2 模块划分

```
ui/            选包 / 扫描预览 / 配置 / 进度 / 结果（Compose 或 WebView 内 HTML）
scanner/       ZipScanner：遍历条目、基名配对、识别 pack.mcmeta、命名空间统计
mapper/        NameMapper：Java→BE 目录与名称映射 + 冲突处理 + 报告
converter/     ChannelConverter：§5 全部公式（纯函数，易单测）
               NormalSplitter：AO/高度/Z 重建
codec/         PngDecoder / TgaEncoder / PackIconGenerator
packer/        ManifestBuilder / TextureSetBuilder / McpackWriter(Zip)
report/        ReportBuilder：输入统计、信息损失、警告、失败清单
bridge/        Android 侧：SAF 文件桥（选入/导出）、进度回调、取消信号
```

**关键设计**：`ChannelConverter` 必须是**无 Android 依赖的纯函数**，这样能在 JVM 上跑单元测试，也能直接复用原型的 JS 版本做交叉验证。

### 6.3 Android 平台约束（2026 现状，检索于 2026-11-15）

| 约束 | 要求 |
|---|---|
| Scoped Storage | **不要申请** `READ/WRITE_EXTERNAL_STORAGE`。用 `ACTION_OPEN_DOCUMENT` 让用户选 zip，拿到 `content://` URI 后立刻拷进 app 私有目录（`Directory.Data`）；导出用 `ACTION_CREATE_DOCUMENT` 或系统分享面板 |
| `MANAGE_EXTERNAL_STORAGE` | 禁止使用 —— Google Play 仅允许文件管理器等少数类目，本 App 会被拒 |
| WebView 本地资源 | Capacitor 3+ / 原生 WebView 走 `WebViewAssetLoader` + `https://app/` 域，不要用 `file:///android_asset/` |
| SDK 版本 | `minSdk 26`（Android 8.0，2026 常见下限）；若上架 Play，**2026-08-31 起新应用/更新须 target API 36（Android 16）** |
| 权限 | 目标 **0 权限**；不需要网络，直接不声明 `INTERNET`，这也顺带兑现「不上传」承诺 |
| 分发 | 侧载用签名的 APK；上架用 AAB。包名建议 `cn.minegraph.pbr2vv` 之类自有命名空间 |

### 6.4 内存与性能（最容易翻车的地方）

Android 上 `ARGB_8888` 位图内存 = `宽 × 高 × 4` 字节；一张 512² 是 1 MB，2048² 是 16 MB。材质包动辄几千张。

- **绝不整包载入**：流式读 ZIP，逐张解码 → 转换 → 编码 → 立刻释放，一张都不留在内存里
- **并发上限 2**（`Dispatchers.IO.limitedParallelism(2)` / JS 侧串行 + `requestAnimationFrame` 让出主线程），避免峰值叠加
- **逐张输出、最后统一打包**，或边转边写 `ZipOutputStream`，避免把所有 TGA 攒在内存
- **尺寸上限**：单张超过 2048² 时提示用户并可选降采样（但降采样会破坏像素艺术，默认拒绝）
- **进度与取消**：每张回调一次，支持中途取消并清理临时文件
- Android 17 的 `MemoryLimiter` 会**静默杀进程**（无 OOM 堆栈），所以宁可慢也要控峰值；用 `getHistoricalProcessExitReasons` 做线上诊断
- 大包建议走前台 Service + 通知，避免切后台被冻结

### 6.5 数据结构

```kotlin
data class ConvertOptions(
    val packName: String,
    val minEngine: IntArray = intArrayOf(1, 21, 120),
    val metalPolicy: MetalPolicy = MetalPolicy.BINARY,
    val emitNormal: Boolean = false,
    val emitSss: Boolean = true,
    val bakeAo: Boolean = false,
    val flipNormalY: Boolean = false,     // 源为 OpenGL 法线时开
    val mapping: Map<String, String> = emptyMap()
)

data class TextureGroup(
    val sourcePath: String,      // assets/minecraft/textures/block/iron_block.png
    val baseName: String,        // iron_block
    val color: ByteArray?,
    val specular: ByteArray?,    // _s
    val normal: ByteArray?,      // _n
    val targetDir: String,       // textures/blocks
    val targetName: String       // 映射后名称
)

data class ConvertReport(
    val total: Int, val converted: Int, val skipped: Int,
    val lostF0Pixels: Long, val lostPorosityPixels: Long,
    val unmappedNames: List<String>, val failures: List<Failure>
)
```

---

## 七、错误处理

| 情况 | 用户提示 | 处理 |
|---|---|---|
| 不是 ZIP / 损坏 | 「文件无法读取」 | 终止，不产出 |
| 无 `pack.mcmeta` | 「未识别为 Java 资源包，仍可强制继续」 | 允许继续，报告标记 |
| 0 张 `_s` | 「没有找到 LabPBR 高光纹理，可能是普通资源包」 | 提供「生成默认 MERS / 写 pbr/global.json」二选一 |
| `_s` 与基色尺寸不一致 | 「X 张尺寸不匹配」 | 跳过该组，记入报告，不拉伸 |
| 单张解码失败 | 「X 张贴图损坏，已跳过」 | 继续整批 |
| 目标名冲突 | 「X 个重名已自动加前缀」 | 命名空间前缀，报告列出 |
| 检测到 OpenGL 法线 | 「法线可能是 OpenGL 格式，是否翻转 Y？」 | 让用户决定，默认不翻 |
| 输出过大 / 空间不足 | 「存储空间不足」 | 清理临时目录，保留已生成部分供分享 |

**原则：单张失败不阻断整批**，所有异常都进报告，导出前展示警告数。

---

## 八、测试策略

| 层级 | 用例 | 验收 |
|---|---|---|
| 单元 · 通道 | `s=255→B=0`、`s=0→B=255`、`s=128→B=63`（精确值 `(1−128/255)²×255=63.25`，原文 `≈64` 为近似）；`g=229→R=0`、`g=230→R=255`；`a=255→G=0`、`a=254→G=255`；`b=64→A=0`、`b=65→A=0`、`b=255→A=255`；金属像素 `A` 强制 0 | 与 §5.1 逐条对齐 |
| 单元 · TGA | 编码后读头：`depth=32 / alpha=8 / y_top=0`；用官方 `iron_block_mers.tga` 反解比对 | `13_` 号 §5.3 |
| 单元 · 法线 Z | 平面法线 (128,128) → Z≈255；X=255 → Z≈128 | `01_` 号公式 |
| 集成 | 用**官方样例包**的 3,171 组做基准：反解其 MERS → 逆推 LabPBR → 再转回，误差 ≤1 | 需要构造反向映射，作为回归基线 |
| 端到端 | 演示包（原型可一键生成）→ `.mcpack` → 用基岩版导入，检查方块反光/发光是否符合预期 | 真机验证 |
| 兼容 | Android 8 / 11 / 14 / 16；16× / 32× / 128× / 512× 材质包；低内存设备 | 不 OOM、不静默被杀 |
| 对照 | 同一输入分别用本 App 与 `Lab2MERS.py` 输出，肉眼比对金属/粗糙度差异 | 应能明显看出平方项差异 |

---

## 九、版本、合规与风险

- **版权**：不内置、不分发任何 Mojang 原版贴图；转换结果由用户对自己的输入负责。App 描述里注明与 Mojang / Microsoft 无隶属关系
- **隐私**：不声明 `INTERNET` 权限，全部处理在设备本地，这既是卖点也是最简单的合规证明
- **版本漂移**：`12_` 号报告指出当前稳定版 1.26.60.5、preview 1.26.70.23，而 `texture_set` 仍是 `1.21.30` schema（`format_version` 是 schema 版本不是游戏版本）。App 应把 schema 版本做成常量表，随版本更新
- **最大未决项**：基岩/VV 法线的 Y 朝向缺 Mojang 官方明文，现有结论（DirectX Y−，与 LabPBR 同向、不翻 G）来自两个第三方转换器实现（`13_` 号 §6.3）。App 必须把 `flip_normal_y` 做成用户可选项，并内置一个「斜射光凹凸自检」提示页
- **次要未决**：稳定版 1.26.60.5 与 preview 的 schema 差异；`pbr/global.json` 在第三方包中的实测行为（官方原版包没有该文件，只能依据文档）

---

## 十、里程碑

| 阶段 | 交付 | 依赖 |
|---|---|---|
| **M0 原型**（本次已交付） | `/workspace/LabPBR2VV/LabPBR2VV.html`：可上传 zip、扫描、配置、真实转换、导出 `.mcpack`，附演示包生成 | — |
| M1 算法固化 | 把原型 JS 移植为无依赖的 Kotlin/Java 纯函数 + 单元测试，用官方样例包做回归 | M0 |
| **M2 Android 壳**（本次已交付骨架，见附录 A） | WebView + SAF 文件桥 + 导出分享，0 权限；工程骨架 `LabPBR2VV/android/`，待本机编译出 APK | M0 |
| **M3 映射表**（本次已交付，见 15 号文档） | 内置 **445 条** Java→基岩映射（覆盖率 74.0%）、自定义覆盖优先、报告命中统计；动画纹理与 `.mcmeta` 保留仍待做 | M0 原型 |
| M4 上架 / 性能 | Capacitor 或原生化、前台 Service、大包内存优化、target API 36、AAB | M3 |

---

## 十一、来源

- 本地资料：`01_LabPBR材质标准.md`（通道定义、金属表、法线 AO/高度、Z 重建公式）、`02_MERS材质标准.md`（TGA 必要性、金属/SSS 互斥）、`05_TextureSet规范.md`（schema、互斥、无效条件）、`12_官方样例包校验报告.md`（实物三件套、manifest、format_version）、`13_纹理文件通道与格式详解.md`（BGRA TGA、位深、法线朝向、pbr fallback）
- 官方规范：<https://learn.microsoft.com/en-us/minecraft/creator/reference/content/texturesetsreference/texturesetsconcepts/texturesetsintroduction>、<https://learn.microsoft.com/en-us/minecraft/creator/documents/rtxpbrintro>
- 官方实物：<https://github.com/Mojang/bedrock-samples/releases>（v1.26.70.23-preview）
- 对照实现：<https://github.com/G2F1SH/Lab2MERS>、<https://github.com/rre36/lab-pbr/wiki>、JE2BE 资源包转换器映射表
- Android 平台：Android Developers《高效加载大型位图》《Bitmaps and memory》、Capacitor / Scoped Storage 文档（检索于 2026-11-15）

---

## 附录 A：路线 A 工程骨架已落地（2026-11-15 追加）

> ⚠️ **状态变更（2026-11-15 晚）**：按用户要求，**整套 APK 工程已移除** —— `android/`（20 个文件）与 `mapping/native_adapter.js`、`sync_assets.py` 已删除，项目收敛为纯网页版形态，`LabPBR2VV.html` 为唯一可运行交付物。以下附录 A 内容保留为**设计史料与当时验证记录**，其中路径均已失效。备份在临时区 `apk_removed_backup.tar.gz`（22 文件），可一键恢复。

M2 的 Android 壳已按 §6.1 路线 A 提前产出工程骨架：**`/workspace/LabPBR2VV/android/`**，完整说明见该目录下 `README.md`。

| 本文条目 | 骨架实现 |
|---|---|
| §6.1「WebView 壳」 | 单个 `MainActivity.kt` + `WebViewAssetLoader`；`assets/www/index.html` = M0 原型 + 末尾原生适配层，**转换算法零改动** |
| §6.3「0 权限 / 不联网」 | Manifest 不声明 `INTERNET` 与任何存储权限；`shouldInterceptRequest` 对非白名单域返回空响应、`shouldOverrideUrlLoading` 拦截外跳 |
| §6.3「Scoped Storage」 | 输入走 `ACTION_OPEN_DOCUMENT`（经 `onShowFileChooser` 透明接管 `<input type=file>`）；输出走 `ACTION_CREATE_DOCUMENT`（JS 桥 `saveFile`） |
| §6.3「不用 file://」 | 入口 `https://appassets.androidplatform.net/assets/www/index.html` |
| §6.3「SDK 版本」 | `minSdk 26` / `targetSdk 36` / `compileSdk 36` / JDK 17 |
| §6.4「内存」 | 首版仍为 JS 串行处理；Base64 桥有约 33% 膨胀，大包需换 `WebMessageListener` 传 ArrayBuffer，或走路线 C 原生化 |

**桥协议**：`AndroidBridge.saveFile(base64, name)` / `AndroidBridge.showToast(msg)` ↔ `JsBridge` 的两个
`@JavascriptInterface` 方法。适配层在普通浏览器里因 `AndroidBridge` 未定义而整块跳过，
因此网页版与 APK **共用同一份引擎源码**（APK 版仅在 `</script>` 前多一段）。
`@JavascriptInterface` 运行在 JavaBridge 线程，启动 SAF 必须切回主线程。

**构建**：Android Studio 打开 `android/`，或 `./gradlew assembleDebug`，产物
`app/build/outputs/apk/debug/app-debug.apk`（已带 debug 签名，可直接侧载）。
Gradle 8.11.1 / AGP 8.9.1 / Kotlin 2.1.0，版本目录在 `gradle/libs.versions.toml`。

**验证状态**：沙箱内用最小 Android API 桩完整编译 `MainActivity.kt`（**0 error**，生成 44 个 class）、
JS 全脚本语法检查通过、转换引擎 **15 项断言全通过**、工程静态一致性 **45 项全通过**；
期间修掉一个真 bug（`colors.xml` 注释含连续连字符 `--` 会导致 aapt 解析失败）。
**沙箱无 Android SDK，未执行 Gradle 构建、未产出 APK、未做真机导入验证** —— 这三项需要本机完成。

### 附录 A 补记：M3 名称映射表（2026-11-15 同批交付）

§5.7 标注为「工程量最大」的映射表已落地，详见 **`15_纹理名映射表.md`** 与
`/workspace/LabPBR2VV/name_map.json`（445 条）。要点：以官方样例包 `texture_set.json` 实物为权威终点，
Java `block/` 仅 56.5% 精确同名；归纳六类规则 + 零歧义 token 推导，覆盖率 74.0%。
网页版原型与 APK `assets` 版均已内联该表（`BUILTIN_MAP`），优先级 **自定义 > 内置 > 原名**，
报告新增 `mapping` 统计。生成与同步脚本在 `LabPBR2VV/mapping/`，换新版样例包可一键重算。

### 附录 A 补记：端到端验证闭环与两个 bug 修复（2026-11-15 同批追加）

§8 里列为待办的「集成测试」与「端到端产物校验」已落地，完整方法与数据见 **`16_端到端转换验证报告.md`**，一键复跑 `cd /workspace/LabPBR2VV && bash verify/run_all.sh`。

| §8 条目 | 本轮结果 |
|---|---|
| 单元 · 通道 | 在真实 Chromium 里跑 **14 项断言全通过**；顺带把 `s=128` 的期望从近似 `≈64` 钉死为精确 **63** |
| 单元 · TGA | 产出 `_mers.tga` / `_normal.tga` 头均为 `type=2 / depth=32 / desc=8`；并与官方 `iron_block_mers.tga` 的 BGRA 首像素 `(191,0,176,0)` 对照一致 |
| 集成 | 官方包 **3,171 组**全量回归：粗糙度、自发光 round-trip 误差 ≤1（达标）；金属度仅 93.34% 达标 —— 官方 **6.84% 像素使用连续金属度**，而 LabPBR `_s` 的 G 通道是二值语义，属规范级损失 |
| 端到端 | 真实浏览器完整跑通「生成演示包 → 载入 → 转换 → 导出」，产出 **15 文件 / 9,927 B** 的 `示例_LabPBR2VV.mcpack`，独立解包 **56 项逐文件校验全通过**（含逐像素比对） |
| 兼容 / 对照 | 静态一致性 **24/24**；网页版与 APK assets 版严格同源 |

**期间修掉两个真 bug**（均已同步到 `android/app/src/main/assets/www/index.html`，并被静态检查 F 组锁死）：

1. **演示包被 canvas 预乘 alpha 破坏（严重）**：原 `makePNG()` 用 `canvas.toBlob()` 生成 PNG，会把 `alpha=0` 像素的 RGB 抹成 0，而 LabPBR `_s` 正是用 alpha 存自发光、RGB 存三个材质通道。演示包里 `demo_metal_s` / `demo_stone_s` 实际退化成 `(0,0,0,0)`，导致金属块与石头的 MERS 全错（`lostF0=256 / lostPorosity=0`，应为 `512 / 512`）。讽刺的是原型 `decodePNG()` 特意绕开 canvas 预乘，生成端却又踩了同一个坑。现改为 `encodePNGBytes()` 用 `CompressionStream('deflate')` 直接写 PNG 字节，零信息损失；启动自检同时检测压缩/解压流。真实用户上传的包由外部工具导出、不经 canvas，转换结果本来就是对的，但演示包是唯一自测入口，必须先修。
2. **`REPORT.output.files` 少算报告自身**：报告在入包前生成，记 `14`，实际 zip 有 `15` 个文件（UI 显示 15），自相矛盾。现于 push 报告 entry 后回填并重写该 entry 字节。

> **APK 状态（已终止）**：沙箱无 Android SDK，从未执行 Gradle 构建、未产出 APK、未做真机导入验证；且整套工程骨架现已按用户要求移除，本条不再有待办。另 `13_` 号附录 A 追加了官方包 23 个上左原点 TGA、常量数组 MERS 引用、连续金属度统计三处实物细节。
