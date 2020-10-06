---
layout: home
---

# Import
## Video:
[![](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/videos/thumbnails/import.png)](https://www.youtube.com/watch?v=MAHPBJdQHCQ&list=PLZlv_N0_O1gZfQaN9qXynWllL7bzX8H3t&index=7)

## Text:

Now let's talk about the import settings. Under the import settings, you can specify what data you want to import from the FBX file.


### Materials:

Whether or not to import the materials from the FBX file.


### Textures:

Whether or not to import the Textures from the FBX file.


### Animation:

Whether or not to import the animation from the FBX file.


### LODs:

Whether or not to import the custom LODs from the FBX file.


NOTE:

In order for this to work properly you must name your associated LOD assets with ‘_LOD<number>’ like in the example below.

![1](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/import/1.png)


### Object name as root bone:

This uses the armature object's name in blender as the root bone name in Unreal.


### Launch FBX Import UI:

When enabled this option launches the FBX import UI in Unreal.


NOTE:

This will launch the Import UI on the first import of the asset, however it will not launch the UI again on a reimport. If you want to reimport a asset with new custom settings, the recommendation is to delete it in your unreal project and then just click ‘Send to Unreal’ again.