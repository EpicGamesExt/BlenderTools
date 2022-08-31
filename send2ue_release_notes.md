## Minor Changes
* Updated _use immediate parent collection name_ to _use immediate parent name_ for broader usage, where the immediate parent can be both a collection or an empty type object
* Refactored _use immediate parent name_ and _use collections as folders_ into **exclusive usage extensions** with LODs and custom collisions support
  * [#352](https://github.com/EpicGames/BlenderTools/issues/352)
  * [#448](https://github.com/EpicGames/BlenderTools/issues/448)
  * [#450](https://github.com/EpicGames/BlenderTools/issues/450)
  * Notes on **exclusive usage extensions**:
    * Exclusive usage extensions cannot be used together, but may be used in combination with other non-exclusive usage extensions.
    * For example, while _use immediate parent name_ can be used in combination with features such as _import lods_ or _combine child meshes_ options, a validation error will be raised if it is used in combination with another exclusive usage extension such as _use collections as folders_
* When _combine child meshes_ is active, meshes without a parent object of the type empty or armature will be exported as usual along with combined meshes
  * [#429](https://github.com/EpicGames/BlenderTools/issues/429)
* Updated test files for extensions for wider testing coverage

## Documentation Changes
* Updated [Extension docs](https://epicgames.github.io/BlenderTools/send2ue/customize/extensions.html)
* Updated [Paths docs](https://epicgames.github.io/BlenderTools/send2ue/settings/paths.html)
* Updated [Supported Extensions docs](https://epicgames.github.io/BlenderTools/send2ue/extras/supported-extensions.html)

## Tests Passing On
* Blender `3.1`, `3.2`
* Unreal `5.0.1`, `5.0.3`

## Special Thanks
* @iigindesign
