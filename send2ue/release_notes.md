## Major Changes
* Added Instance Assets Extension. Read more [here](https://epicgames.github.io/BlenderTools/send2ue/extensions/instance-assets)
  * [579](https://github.com/EpicGames/BlenderTools/issues/579)

## Minor Changes
* Fixed unreal api change for removing lods.
  * [586](https://github.com/EpicGames/BlenderTools/issues/586)
* Fixed error when attempting to remove or add affixes on empty material slot.
  * [455](https://github.com/EpicGames/BlenderTools/issues/455)
* Fixed local rotation axis for static mesh sockets.
  * [592](https://github.com/EpicGames/BlenderTools/issues/592)
* Fixed AttributeError "NoneType" has no Attribute "matrix_world".
  * [598](https://github.com/EpicGames/BlenderTools/issues/598)
* Fixed root motion scale when importing assets into blender.
  * [597](https://github.com/EpicGames/BlenderTools/issues/597)
* Added validation to check for vertex groups on meshes that are assigned to an armature.
  * [585](https://github.com/EpicGames/BlenderTools/issues/585)

## Tests Passing On
* Blender `3.3`, `3.5` (installed from blender.org)
* Unreal `5.1`
