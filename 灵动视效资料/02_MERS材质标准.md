# MERS材质标准

> 来源：<https://docs.minegraph.cn/mersmaterialstandard.html>
> 整理日期：2026-11-15　|　原文语言：中文
> 说明：由原始网页自动整理为 Markdown，仅供离线查阅，请以原文为准。

---

# MERS 材质标准

MERS （金属-自发光-粗糙度-次表面散射）是 Java 版 即将到来 与基岩版官方光影包灵动视效（暂译，Vibrant Visuals）所使用的 PBR 材质标准。与 [LabPBR](https://docs.minegraph.cn/labpbrmaterialstandard.html) 的 `_s` 纹理类似，MERS 纹理保存了各种 PBR 信息以供光影使用。

MERS 顾名思义，其按照名字逐通道存储了下列 PBR 信息：

- 红色通道：金属度（Metalness），0 为非金属，255 为金属；
- 绿色通道：自发光强度（Emissive），0 为不发光，255 为最大发光；
- 蓝色通道：粗糙度（Roughness），0 为完全光滑，255 为完全粗糙；
- Alpha 通道：次表面散射强度（Subsurface scattering），0 为无散射，255 为最大散射。

金属与次表面散射效果互斥，游戏会优先选择两者的大值处理对应效果，并在两者强度相同时优先使用次表面散射。

> 和 LabPBR 不同的是，Alpha 通道的次表面散射强度在值为 0 与 255 时仍然按照预期工作，因此对于大多数弱次表面散射物体，PBR 纹理在资源管理器中预览起来都是透明的。不仅如此，由于一些绘图工具（比如 Photoshop）对 PNG 格式的优化，会导致 Alpha 为 0 的区域丢失 RGB 数据，因此只能使用 TGA 格式。

## LabPBR 转 MERS 工具

本工具由 江原心咲 与 Shulker 主导开发，旨在将 Java 版 OptiFine/Iris 光影社区现行的 PBR 格式 LabPBR 快速便捷地转换到灵动视效中 PBR 所使用的 MERS 格式。

[GitHub 仓库](https://github.com/G2F1SH/Lab2MERS)

29 April 2026

[LabPBR 材质标准](https://docs.minegraph.cn/labpbrmaterialstandard.html)[作品开发相关资料](https://docs.minegraph.cn/developtips.html)
