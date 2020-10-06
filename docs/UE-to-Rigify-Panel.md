---
layout: home
---

# UE to Rigify Panel
This section defines all the properties and operators depicted below in the ‘UE to Rigify’ panel in the 3D viewport.

![1](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/ue_to_rigify_panel/1.png)![2](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/ue_to_rigify_panel/2.png)![3](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/ue_to_rigify_panel/3.png)![4](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/ue_to_rigify_panel/4.png)

### Source

This object picker specifies which object is the ‘Source’ rig.


### Template

This dropdown allows you to select a template or create a new one.


### Mode

This dropdown allows you to select which mode you want to edit your rig template in. The ‘UE to Rigify’ modes are: ‘Source’, ‘Edit Metarig’, ‘FK to Source’, ‘Source to Deform’, and ‘Control’.


### Overwrite Animation

If enabled, your control rig animation data will be overwritten by the animation data from your source rig.


### Metarig

This dropdown gives you some metarig presets that you can use as starting points when creating your new metarig template.


### Name

This property defines the name of your new rig template.


### Save Metarig

This operator saves the state of your current metarig into the rig template file, and switches the mode back to ‘Source’ mode.


### Save Nodes

This operator saves the state of your current node tree into the rig template file, and switches the mode back to ‘Source’ mode.


### Convert

This operator switches the current mode to ‘Control’ mode, builds the Rigify rig, and constrains the ‘Source’ rig bones to it.


### Revert

This operator switches the current mode to ‘Source’ mode, and restores the view to just the ‘Source’ rig.


### Bake

This operator bakes the ‘Control’ rig actions to the ‘Source’ rig actions.