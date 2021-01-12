---
layout: default
folder: ""
---

# Import
<iframe src="https://www.youtube.com/embed/MAHPBJdQHCQ" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>



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

![1]( {{ '/assets/images/send2ue/preferences/import/1.jpg' | relative_url }} )


### Sockets:

Imports an empty as a socket as long as it is a child of a mesh and its name starts with 'SOCKET_'. (Only works on static meshes)

![2]( {{ '/assets/images/send2ue/preferences/import/2.jpg' | relative_url }} )

### Object name as root bone:

This uses the armature object's name in blender as the root bone name in Unreal.


### Launch FBX Import UI:

When enabled this option launches the FBX import UI in Unreal.


NOTE:

This will launch the Import UI on the first import of the asset, however it will not launch the UI again on a reimport. If you want to reimport a asset with new custom settings, the recommendation is to delete it in your unreal project and then just click ‘Send to Unreal’ again.
