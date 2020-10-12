---
layout: default
folder: ""
---

# FAQ

### How do you send a mesh from blender to unreal?
First make sure your mesh is under the ‘Mesh’ collection, then can do this by clicking in the Blender header menu Pipeline > Export > Send to Unreal.


### How do you import bones with the correct scale from blender to unreal?
First your rig object needs to have the right scale to begin with, so if you are importing an FBX that was exported from Unreal, use the [Import Asset](./Import-Asset) operator. This will ensure your rig comes into Blender scaled correctly. Also before you export you need to make sure you rig object's scale is 1. You can do this by applying the transformations on your armature object and its child objects. Also ensure that [Automatically Scale Bones](./Export#automatically-scale-bones) is turned on in the 'Export' options. Remember, ultimately, the dimensions are the real size of an object, not the scale factor.

### Can I have multiple Unreal editors open at once and use 'Send to Unreal'?
Currently, no. 'Send to Unreal' connects to the first Unreal editor process on your OS. So there isn't a good way of specifying which Unreal editor instance to connect to at the moment. There are plans to support this is the future though.