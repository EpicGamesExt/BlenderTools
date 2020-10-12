---
layout: default
folder: ""
---

# Errors

### You do not have the correct objects under the "Mesh" or "Rig" collections or your rig does not have any actions to export!

You could receive this error if you did not move the objects you wanted to export under the ‘Mesh’ or ‘Rig’ collections, or if you moved the wrong object types under those collections, or if you hid all your objects under those collections.  This will also be thrown if you are trying to export just a rig object with no mesh and it does not have any animation data, or it’s animation data is muted.


### Mesh `<mesh name>` has no geometry.

This will be thrown if you are trying to export an object of type ‘Mesh’ that has no vertices.


### The mesh folder `<your path>` does not exist! Please make sure that the path under "Mesh Folder (Disk)" was entered correctly!

This will be thrown if you enter a path to a mesh folder that does not exist on disk.


### The mesh folder `<your path>` does not exist! Please make sure that the path under "Animation Folder (Disk)" was entered correctly!

This will be thrown if you enter a path to an animation folder that does not exist on disk.


### There is no skeleton in your unreal project at: `<your project path to the skeleton>`.

This will be thrown if you have entered a skeleton asset path to a skeleton that does not exist in your unreal project, or you are trying to do a animation only import an a skeleton asset can not be found in your project under the “Mesh Folder (Unreal)” that matches the name of the asset plus ‘_Skeleton’.


### Object `<mesh name>` does not follow the correct naming conventions for LODs.

This is being thrown because you have the the ‘LODs’ option enabled under your import settings, but not all the objects under the Mesh collection follow the correct naming convention for LODs. The correct convention is ‘<asset name>_LOD<number>’


### Mesh `<mesh name>` has a unused material `<material slot>`

This specified mesh did not pass the ‘Check for unused materials’ validation.


### Mesh `<mesh name>` has a material `<material name>` that contains a missing image `<image>`.

This specified mesh did not pass the ‘Check texture references’ validation.

### You do not have a collection `<collection_name>` in your scene! Please create it!

You need to create the missing collection manually in the outliner, Or hit "M" and click "Create New Collection".

