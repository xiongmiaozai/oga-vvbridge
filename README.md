# LabPBR2VV

Java 版 LabPBR 材质包 → 基岩版 **灵动视效（Vibrant Visuals）** `.mcpack` 的离线转换器。

## 目录结构

- `LabPBR2VV/LabPBR2VV.html` — 单文件离线转换器（浏览器打开即可用）
- `LabPBR2VV/name_map.json` — 纹理名映射表（484 条）
- `LabPBR2VV/mapping/` — 映射表生成脚本与官方资源清单
- `LabPBR2VV/verify/` — 端到端验证与静态检查脚本
- `灵动视效资料/` — 规范、结构分析、排障专题与对比图（01–28，含 README 索引）

## 核心能力

- LabPBR `_s` / `_n` → MERS（金属度 / 自发光 / 粗糙度 / SSS）转换，非预乘 alpha
- 自动扫描、命名映射、目录重定向、`.tga` 格式优先级处理
- Java overlay 叠加层烘焙（如草侧面）、床 UV 重排、铁砧/矮草等命名修复
- `manifest.json` / `*.texture_set.json` 生成与多语言简介，一键打包 `.mcpack`

大体积产物（`.mcpack` / `.zip`）不入库，由转换器生成或单独分发。
