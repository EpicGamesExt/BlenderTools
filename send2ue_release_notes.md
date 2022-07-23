## Minor Changes
* Static mesh with modifier is not affixed
  * https://github.com/EpicGames/BlenderTools/issues/467
* Refactored combine meshes logic into an extension
  * https://github.com/EpicGames/BlenderTools/issues/459
* Refactored object origin logic into an extension
* Added `filter_objects` method to extension class interface
    * This allows extension classes to filter out mesh object or armature object during the collection phase

* Fixed bug that was freezing the viewport when displaying a validation message.

## Tests Passing On
* Blender `3.1`, `3.2`
* Unreal `5.0.1`
