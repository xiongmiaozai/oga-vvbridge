# Cubemaps（天空盒 / 环境反射）

**状态：本目录不提供完整配置模板。** 原因：Mojang 官方样例包 `bedrock-samples v1.26.70.23-preview` 中**未附带任何 cubemaps/*.json 实例**，本地只有 biome 侧的标识符 schema（见下），拿不到权威的字段结构。凭空编造字段会导致资源包报错，因此这里只给出"如何接入"的确凿部分。

## 已确凿的信息（来自官方样例包 schema）

- 目录名：`cubemaps/`
- 在 client biome 中通过组件引用：

```json
"minecraft:cubemap_identifier": {
  "cubemap_identifier": "pbr2vv:my_cubemap"
}
```

- 官方 schema `metadata/json_schemas/client/biome/1.21.130/minecraft_cubemap_identifier.json` 的原文描述：
  > Set the identifier used for cubemap in Vibrant Visuals mode. Identifiers must resolve to identifiers in valid Cubemap JSON schemas under the "cubemaps" directory. Biomes without this component will have default cubemap settings.

- 该组件自 **1.21.130** 起出现在 schema 中（比另外四类更新）。

## 如何补齐

如需使用 cubemap 配置，请查官方文档（本库 `07_生物群系自定义.md` 第 26 行给出了链接）：

- <https://learn.microsoft.com/en-us/minecraft/creator/documents/vibrantvisuals/cubemapcustomization?view=minecraft-bedrock-experimental>

最稳妥的做法：在 **Bedrock Editor** 里打开 Vibrant Visuals Settings，添加 cubemap 配置，用编辑器的"复制 JSON / 生成资源包"功能拿到官方生成的合法 schema，再据此改自己的参数。
