## Minor Changes
* Fixed static mesh with modifier not affixed
  * https://github.com/EpicGames/BlenderTools/issues/467
* Refactored combine meshes logic into an [extension](https://epicgames.github.io/BlenderTools/send2ue/extras/supported-extensions.html#combine-meshes)
  * https://github.com/EpicGames/BlenderTools/issues/459
* Refactored object origin logic into an [extension](https://epicgames.github.io/BlenderTools/send2ue/extras/supported-extensions.html#object-origin)
* Added `filter_objects` method to extension class interface
    * This allows extension classes to filter out mesh objects or armature objects during the collection phase
* Fixed bug that was freezing the viewport when displaying validation messages.

## Deprecated
Combine child meshes does not combine children of mesh objects, rather it only
combines children of an empty or an armature now. Read [here](https://epicgames.github.io/BlenderTools/send2ue/extras/supported-extensions.html#combine-meshes) for more info.

## Tests Passing On
* Blender `3.1`, `3.2`
* Unreal `5.0.1`

## Special Thanks
* @Seekon
* @iigindesign
