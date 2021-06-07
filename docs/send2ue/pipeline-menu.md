---
layout: default
folder: ""
---
# Pipeline Menu

## Import

### Import Asset

The Asset importer allows you to import assets then run a series of operations on them to fix them.  The series of operations run on the imported asset depends on what source application you select from the drop down. A source application is the application the original file was generated in. Currently, the only supported source application is *Unreal Engine 4*.

After the selected FBX file is imported the imported action location f-curves are scaled up to a match the scene scale factor with a scale of 1, the objects are applied with a scale factor of 1. The scaled keyframes on the root object are removed, and the keyframes are rounded to the nearest integer based on the current frame rate.

![1]( {{ '/assets/images/send2ue/pipeline-menu/1.jpg' | relative_url }} )

## Export

### Send to Unreal

This operator quickly sends your assets to an open unreal editor instance without invoking a dialog. The settings used for the operation are defined in the addon preferences.

![2]( {{ '/assets/images/send2ue/pipeline-menu/2.jpg' | relative_url }} )

### Advanced Dialog

This operator invokes a dialog that gives you quick access to the settings in the send to unreal addon preferences. Once 'OK' is selected your assets will be sent to the first open unreal editor instance and imported. The settings modified here are also modified in the addon preferences. Any changes to the addon preferences are saved into the .blend on a file save event.

![3]( {{ '/assets/images/send2ue/pipeline-menu/3.jpg' | relative_url }} )

## Affixes

### Add Asset Affixes

Adds the affixes (prefix/suffix) by renaming all assets that are currently selected for export by being in the Mesh collection.

> NOTE: This will rename the objects in Blender, like Meshes, Textures, Materials and Actions. Be aware that this will also rename the texture image files on your hard-disk.

### Remove Asset Affixes

Removes the affixes (prefix/suffix) by renaming all assets that are currently selected for export by being in the Mesh collection.

> NOTE: This will rename the objects in Blender, like Meshes, Textures, Materials and Actions. Be aware that this will also rename the texture image files on your hard-disk.

## Create Pre-Defined Collections

Manually triggers the creation of the collections required for the export (‘Mesh‘, ‘Rig‘, ‘Collision‘, ‘Extras’).
