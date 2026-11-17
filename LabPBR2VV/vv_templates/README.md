# 灵动视效（VV）可编辑配置模板

> 生成日期：2026-11-16　|　依据：Mojang 官方样例包 `bedrock-samples v1.26.70.23-preview-full.zip` 实物（172MB）中的真实配置文件 + 官方 `07_生物群系自定义.md` 文档。
> 所有模板的字段结构均来自官方包实例，未凭空捏造；identifier 改为 `pbr2vv:` 命名空间以避免与官方 `minecraft:` 默认值冲突。

## 一、除贴图外，灵动视效包里到底能编辑什么

一个 VV 资源包分两大块：**贴图层**和**配置层**。转换器目前只做贴图层，下面是配置层（即"除贴图外"）的完整清单。

| 类别 | 目录 / 文件 | 能编辑什么 | 混合方式 |
|---|---|---|---|
| **大气** atmospherics | `atmospherics/*.json` | 天空天顶/地平线色、瑞利强度、太阳/月亮 Mie 强度、太阳光晕、地平线混合停靠点 | 按玩家位置空间混合 |
| **光照** lighting | `lighting/*.json` | 太阳/月亮照度与颜色（关键帧）、点闪光 flash、环境光、天空强度、自发光去饱和 | 按玩家位置空间混合；`orbital_offset_degrees` 全包须一致 |
| **色彩分级** color_grading | `color_grading/*.json` | 对比度/增益/伽马/偏移/饱和度（midtones）、色温、`tone_mapping.operator` | 按玩家位置空间混合；tone mapping 算子全包须一致 |
| **水体** water | `water/*.json` | 颗粒浓度（叶绿素/泥沙/CDOM）、焦散、波浪参数 | 按水体几何位置混合；caustics 与 waves 开关全包须一致 |
| **天空盒** cubemaps | `cubemaps/*.json` | 环境反射天空盒（1.21.130+） | 本目录暂无权威模板，见 `cubemaps/README_cubemaps.md` |
| **群系绑定** client_biome | `biomes/*.client_biome.json` | 用 `minecraft:*_identifier` 组件把上面几类配置挂到具体群系 | — |
| **全局回退** pbr | `pbr/global.json` | 无 `_s` 贴图的金属/自发光/粗糙/SSS 默认值 | 全局单例，两包都定义会冲突 |

## 二、关键机制（来自官方 07 号文档）

1. **一个类别可放多个实例**，只要文件名唯一、JSON 内 `identifier` 唯一。
2. **保留文件名 = 全局默认**：`atmospherics/atmospherics.json`、`color_grading/color_grading.json`、`lighting/global.json`、`water/water.json` 里的 identifier 会自动作为全局默认，除非某个 biome 显式指定别的。
3. **1.21.90 起**原版包自带逐群系配置，优先级高于内置全局值和自定义包的全局文件。想给群系上自定义视觉，必须在 client biome JSON 里用对应命名空间指定。
4. **时间关键帧**：数值既可写单个数字，也可写成 `{"时间点": 值}` 的对象；时间点 0=正午、0.25=日落、0.5=午夜、0.75=日出、1=次日正午，引擎线性插值。
5. **不能混合的参数**（一个包内所有同类 schema 必须一致）：tone mapping 算子、orbital offset 角度、caustics 参数、waves 开关。

## 三、这些模板怎么用

- **方式 A（推荐，无需背 schema）**：在 **Bedrock Editor** 打开 Vibrant Visuals Settings 图形界面调整 → 一键生成资源包 / 复制 JSON。本目录模板可作为起点对照。
- **方式 B（手动）**：把本目录的 `atmospherics/`、`lighting/`、`color_grading/`、`water/`、`biomes/` 子目录整体拷进你的 VV 资源包根目录，按需改数值；再在 `biomes/example.client_biome.json` 里把群系 identifier 换成目标群系。

## 四、与本项目转换器的关系

转换器 `LabPBR2VV.html` 输出的包目前**只含贴图层**（`textures/` + texture_set + MERS + 可选 `pbr/global.json` 回退），不含上述配置层——因为 Java LabPBR 贴图里没有这些光源/大气数据，无法自动转换。本目录提供的是**可编辑的空模板/官方默认值副本**，供玩家在转换后再手动追加，实现"贴图 + 光影"完整效果。

如需把它们合并进转换后的包，可自行解包 `.mcpack` → 拷入这些目录 → 重新打包为 `.mcpack`（保持 manifest 在根目录）。注意遵守上面第 2 节的"全包一致"约束，避免叠加报错。
