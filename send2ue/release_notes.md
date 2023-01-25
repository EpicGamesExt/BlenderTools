## Major Changes
* Send to Unreal is no longer using the blender FBX export operator. Instead, it uses a patched version of the logic in
the `export_fbx_bin` module from Blender's FBX addon. The reasoning for doing this was to fix the scale factor that gets baked
into exported FBX files for SkeletalMesh and AnimSequence assets at the FBX level rather than fixing this issue by preforming operations to the blender scene and objects.
(This logic was quite complex and still imposed some limitations. Now it can all be removed!). It should be noted that this change is substantial, and while we have done our best to test
this, it could introduce some new bugs that were overlooked. If there are issues with the scale, please report any issues and roll back to version `2.2.1` of the addon in the meantime.
* `Use object origin` is now a core feature. This now uses the FBX export module to set the world location of StaticMesh, SkeletalMesh, and AnimSequence assets. This fixes some
common problems that were introduced by moving objects in the blender scene pre-export.
* The `Sync control rig tracks to source rig` option has been added back to the ue2rigify extension. Since the `Automatically scale bones` feature has been removed, it made it easy to
add this option back in as an extension.
  * [#417](https://github.com/EpicGames/BlenderTools/issues/417)

## Minor Changes
* "Send to Unreal" button in settings dialog was renamed to "Push Assets" to be more accurate since the tool can also
only export to disk if used in that mode.
* `Check scene scale` no longer has an option for 0.01. It no only checks for a scene scale of 1 since this is the only
recommend way to work.

## Deprecated
* The option `Automatically scale bones` has been removed. This was the default option that fixed the scale factor in
SkeletalMesh and AnimSequence assets by scaling the object, scene, and fcurves. This is no longer needed since this is handled in the FBX export now.
* The `Use object origin` extension has been removed since it is now a core feature.

## Tests Passing On
* Blender `3.3`, `3.4`
* Unreal `5.1`
