# PBR概览

> 来源：<https://learn.microsoft.com/en-us/minecraft/creator/documents/rtxpbrintro?view=minecraft-bedrock-stable>
> 整理日期：2026-11-15　|　原文语言：英文
> 说明：由原始网页自动整理为 Markdown，仅供离线查阅，请以原文为准。

---

# Overview of Physically Based Rendering

Physically Based Rendering, or PBR, simulates how materials would react to realistic light behavior. Metallic surfaces cast reflections; light bends and refracts through different types of glass. Minecraft's Vibrant Visuals and ray tracing graphics modes both utilize this modern graphics technique to enhance in-game visuals. For objects you create to take advantage of PBR, you'll need to create special textures that capture properties of the material, such as metallic properties, emissive properties, and roughness (often abbreviated together as "MER"). In Vibrant Visuals, an extra channel has been added for subsurface scattering properties; all together, these are known as "MERS."

By the end of this overview, you'll learn:

- The new texture maps available in Minecraft: Bedrock Edition.
- The basic workflows when designing PBR textures for Minecraft.
- How to create a mirror texture set using roughness and metallic maps.

## Prerequisites

It'll be helpful to have read the [Introduction to Resource Packs](https://learn.microsoft.com/en-us/minecraft/creator/resourcepack?view=minecraft-bedrock-stable) before reading this document. You'll need a ready-to-go Resource Pack with the `textures/blocks` folder structure set up.

While we'll provide textures to download, you'll need to have some digital painting software that has layers to create your textures, such as the Windows 11 version of Microsoft Paint, Adobe Photoshop, or PaintTool SAI. Blockbench, a Minecraft favorite for creating 3D models, also has a PBR-specific plugin that makes creating and exporting MER textures a breeze.

## What makes a PBR texture?

In Minecraft, 3D models are given detail by applying 2D images to them using a common rendering method called **Texture Mapping**. Standard Minecraft blocks use a single texture map, an image with four color channels: Red, Blue, Green, and Alpha (RGBA). Most image editors work with RGBA images: the first three channels provide the color for each image pixel, while the alpha channel controls that pixel's transparency level.

PBR introduces *new* maps for textures that set values for different kinds of properties for each pixel in the color map:

- [Metalness Map](https://learn.microsoft.com/en-us/minecraft/creator/documents/rtxpbrintro?view=minecraft-bedrock-stable#metalness-map)
- [Emissive Map](https://learn.microsoft.com/en-us/minecraft/creator/documents/rtxpbrintro?view=minecraft-bedrock-stable#emissive-map)
- [Roughness Map](https://learn.microsoft.com/en-us/minecraft/creator/documents/rtxpbrintro?view=minecraft-bedrock-stable#roughness-map)
- [Normal Map](https://learn.microsoft.com/en-us/minecraft/creator/documents/rtxpbrintro?view=minecraft-bedrock-stable#normal-map)
- [Height Map](https://learn.microsoft.com/en-us/minecraft/creator/documents/rtxpbrintro?view=minecraft-bedrock-stable#height-map)

And specifically in Vibrant Visuals, another property is available for:

- [Subsurface Scattering](https://learn.microsoft.com/en-us/minecraft/creator/documents/subsurfacescatteringcustomization?view=minecraft-bedrock-stable)

Together, these maps give you a great deal of control over how models you add to your resource packs are rendered when placed in the world. Note that in ray traced modes, PBR textures are only supported for blocks; in Vibrant Visuals, these properties can also be applied to mobs, items, and particles. Let's look at each kind of map in turn.

Important

Not all PBR texture sets require all maps. Leaving empty maps will cause the texture set to use the default value.

### Metalness map

A Metalness map is a grayscale texture that determines which areas of a texture map look like metal. The brighter the pixel is, the more metallic it will look.

- A pixel set to pure black is completely non-metallic, with a value of `0.0`. Grass, dirt, and tree bark are completely non-metallic objects.
- A pixel set to pure white is completely metallic, with a value of `1.0`. Iron, gold, and copper are examples of completely metallic objects.
- Pixels between pure black and pure white will look more or less metallic, depending on how bright or dark they are.

![concrete white block with metallic edges and a matte center](https://learn.microsoft.com/en-us/minecraft/creator/media/rtx/concrete_metallic_example.png?view=minecraft-bedrock-stable)

The above image uses the following metalness map:

![concrete white block metallic mer texture](https://learn.microsoft.com/en-us/minecraft/creator/media/rtx/texture/metallic_mer.png?view=minecraft-bedrock-stable)

### Emissive map

An Emissive map is a grayscale texture that determines which areas of a texture map emit light.

- A pixel set to pure black is completely non-emissive (dark), with a value of `0.0`.
- A pixel set to pure white is completely emissive (glowing at its brightest), with a value of `1.0`.
- Pixels between pure black and pure white will glow more or less brightly, depending on how bright or dark they are.

![concrete white block with vertical glowing stripes](https://learn.microsoft.com/en-us/minecraft/creator/media/rtx/concrete_emissive_example.png?view=minecraft-bedrock-stable)

The above image uses the following emissive map:

![concrete white block emissive mer texture](https://learn.microsoft.com/en-us/minecraft/creator/media/rtx/texture/emissive_mer.png?view=minecraft-bedrock-stable)

### Roughness map

A Roughness map is a grayscale texture that determines which areas of the texture map are smooth and which are rough.

- A pixel set to pure black is as smooth as possible, with a value of `0.0`. Smooth marble, glass, or smooth plastic are very smooth.
- A pixel set to pure white is as rough as possible, with a value of `1.0`. Brick, tree bark, and stones are very rough.
- Pixels between pure black and pure white will look more or less rough, depending on how bright or dark they are.

![concrete white block with horizontal rough and smooth stripes](https://learn.microsoft.com/en-us/minecraft/creator/media/rtx/concrete_rough_example.png?view=minecraft-bedrock-stable)

The above image uses the following roughness map:

![concrete white block roughness mer texture](https://learn.microsoft.com/en-us/minecraft/creator/media/rtx/texture/rough_mer.png?view=minecraft-bedrock-stable)

### Normal map

A [Normal map](https://en.wikipedia.org/wiki/Normal_mapping) is an RGB texture (not grayscale) that controls the depth and how light behaves when a light ray hits the texture. "Normal" refers to the concept of [a surface normal in geometry](https://en.wikipedia.org/wiki/Normal_(geometry)), and the R, G, and B elements in the normal map correspond to the X, Y, and Z coordinates of the surface. Values of R (X) 128, G (Y) 128, and B (Z) 255 result in a flat appearance of the pixel.

Caution

Unless you have experience with creating Normal maps, it's recommended that you do not create Normal maps by hand. Third-party software is available to assist with creating Normal maps.

### Height map

A Height map is a grayscale texture that controls depth of a texture. Height maps act as an alternative to Normal maps, but are not as efficient and cannot represent as many textures.

- A pixel set to pure black extrudes inward as much as possible, with a value of `0.0`.
- A pixel set to pure white extrudes outward as much as possible, with a value of `1.0`.
- A pixel midway between pure black and pure white (127, 127, 127), with a value of `0.5`, does not extrude in or out.

![concrete white block that has ridges in a square pattern](https://learn.microsoft.com/en-us/minecraft/creator/media/rtx/height_example.png?view=minecraft-bedrock-stable)

The above image uses the following height map:

![concrete white block height mer texture](https://learn.microsoft.com/en-us/minecraft/creator/media/rtx/texture/height_map.png?view=minecraft-bedrock-stable)

## Make a mirror

Let's create a mirror texture for an existing vanilla block by creating a Texture Set JSON file and using a provided texture file.

### Make a texture set JSON

For the Texture Set to work properly, you will need to define a JSON file to load the textures. This tutorial is a mirror example working with the **iron\_block** block.

Tip

To learn more about texture sets, please read [Introduction to Texture Sets](https://learn.microsoft.com/en-us/minecraft/reference/content/texturesetsreference/texturesetsconcepts/texturesetsintroduction?view=minecraft-bedrock-stable).

1. In your behavior pack, navigate to the `textures/blocks` folder.
2. Create a new .JSON file and name it `iron_block.texture_set.json`.
3. Double-click on `iron_block.texture_set.json` to edit the contents.
4. Copy the following example into the file:

   ```
   {
     "format_version": "1.16.100",
     "minecraft:texture_set": {
       "color": "iron_block",
       "metalness_emissive_roughness": "iron_block_mer"
     }
   }
   ```

More examples of texture set files with different configurations, specifying MERS properties with hardcoded values, or adding subsurface scattering properties to your object can also be found on the above mentioned [Introduction to Texture Sets](https://learn.microsoft.com/en-us/minecraft/reference/content/texturesetsreference/texturesetsconcepts/texturesetsintroduction?view=minecraft-bedrock-stable) page.

5. Save and close the file.

With the JSON file set up, you can now configure the textures for the `color` values and the `metalness_emissive_roughness` values.

### Add the PBR capability

The **manifest.json** file for the pack requires the value `"pbr"` or `"raytraced"` to be added in a `capabilities` section below your existing `header` and `modules` in order to unlock compatability with Vibrant Visuals or ray traced rendering modes:

```
{
    "format_version": 1,
    "header": {
        "name": "My Sample Resources",
        "description": "",
        "uuid": "58d4560c-106d-4b0c-9847-eee47417fb05",
        "min_engine_version": [1, 21, 120],
        "version": [1, 0, 0]
    },
    "modules": [
        {
            "description": "",
            "type": "resources",
            "uuid": "2d3df25b-856a-406d-9a57-c87b9a4d7af8",
            "version": [0, 0, 1]
        }
    ],
    "capabilities" : [
        "pbr", // Add for support in Vibrant Visuals rendering mode
        "raytraced" // Add for support in ray traced rendering mode
    ]
}
```

### Add the textures

To create a mirror in a PBR workflow, you need a Roughness map and a Metalness map. A Roughness map with a value of `0.0`, or solid black, will create a smooth surface for light to reflect off. A Metalness map set to a value of `1.0`, or solid white, will render the block like reflective metal.

Download these two PNG files, **iron\_block.png** (the color texture map) and **iron\_block\_mer.png** (the MER texture map), by right-clicking them and selecting **Save image as**:

- ![](https://learn.microsoft.com/en-us/minecraft/creator/media/rtx/texture/iron_block.png?view=minecraft-bedrock-stable)
  iron\_block.png
- ![](https://learn.microsoft.com/en-us/minecraft/creator/media/rtx/texture/iron_block_mer.png?view=minecraft-bedrock-stable)
  iron\_block\_mer.png

Copy and paste both **.png** files into the **textures/blocks** folder.

## Run the texture pack

With the JSON file properly set up and both textures in place, you can now load in your texture pack to test in Minecraft. Note that you will need a compatible machine to run Vibrant Visuals or ray traced graphics modes.

![iron block reflecting flowers from the environment](https://learn.microsoft.com/en-us/minecraft/creator/media/rtx/mirror.png?view=minecraft-bedrock-stable)

## What's next?

- Learn how to [use Blockbench to create MER-mapped models](https://learn.microsoft.com/en-us/minecraft/creator/documents/useblockbenchtocreatemodelswithtextures?view=minecraft-bedrock-stable).
- Learn about [Lighting Customization](https://learn.microsoft.com/en-us/minecraft/creator/documents/lightingcustomization?view=minecraft-bedrock-stable).
- Control the in-game appearance of [Fog](https://learn.microsoft.com/en-us/minecraft/creator/foginresourcepacks?view=minecraft-bedrock-stable) using a similar JSON structure.

---

## Feedback

Was this page helpful?

No

Need help with this topic?

Want to try using Ask Learn to clarify or guide you through this topic?

---

## Additional resources
