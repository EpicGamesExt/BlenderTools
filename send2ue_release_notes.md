## Minor Changes
* Updated use_immediate_parent_collection_name to use_immediate_parent_name for broader usage, where the immediate parent can be both a collection and empty type object
* Refactored use_immediate_parent_name and use_collections_as_folders into exclusive usage extensions with LODs and custom collisions support
  * [#448](https://github.com/EpicGames/BlenderTools/issues/448)
  * Notes on exclusive usage extensions:
    * Exclusive usage extensions cannot be used together, but may be used in combination with other non-exclusive usage extensions.
    * For example, while use_immediate_parent_name can be used in combination with features such as import_lods or combine_meshes options, a validation error will be raised if it is used in combination with another exclusive usage extension such as use_collections_as_folders.
* Updated extensions and settings > paths documentations


## Tests Passing On
* Blender `3.1`, `3.2`
* Unreal `5.0.1`, `5.0.3`

## Special Thanks
* @iigindesign
