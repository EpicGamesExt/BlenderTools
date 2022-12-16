## Major Changes
* [#354](https://github.com/EpicGames/BlenderTools/issues/354) **Alembic to Groom** Pipeline
  * Tool supports automated export + import of the alembic to groom translation from blender to UE; Latest changes from [blender 3.3](https://www.blender.org/download/releases/3-3/) (new Curves object type, sculpt workflow) are supported along with the previous particle hair workflow
* Extensions updated/created for Groom
  * The _Combine Meshes_ extension is renamed to _Combine Assets_, which now supports various ways to combine groom assets upon export; it remains compatible with paths extensions
    * This extension has six combine options: 'off', 'child_meshes', 'groom per mesh', 'groom per combined mesh', 'all grooms and child meshes' and 'all grooms'
  * A new extension called _Create Post Import Assets For Groom_ is added with two options: 'create binding asset' and 'create blueprint asset for groom' that support automatic UE asset creation according to the imported assets
    * 'create binding asset' creates a groom binding asset in unreal complete with the imported groom asset and a target skeletal mesh
    * 'create blueprint asset for groom' creates a blueprint asset with a skeletal mesh component and its associated groom components, populated with imported groom and mesh assets

## Minor Changes
* Added two new import options toggles ('import_grooms' and 'import_meshes') to allow further customization for assets imported from the 'Export' collection
* Added validation to check for required unreal plugins
* Increased testing coverage for the groom workflow and new extensions

## Documentation Changes
* New [Groom Asset Type](https://github.com/EpicGames/BlenderTools/docs/send2ue/asset-types/groom.html) Page
* New [_Combine Assets_](https://github.com/EpicGames/BlenderTools/docs/send2ue/extensions/combine-assets.html) Extension Page
* New [_Create Post Import Assets For Groom_](https://github.com/EpicGames/BlenderTools/docs/send2ue/extensions/create-post-import-groom-assets.html) Extension Page
* Restructured multiple doc hierarchies to improve readability
* Modified [Import Settings](https://github.com/EpicGames/BlenderTools/docs/send2ue/settings/import.html) Page

## Tests Passing On
* Blender `3.3`
* Unreal `5.1`

## Special Thanks
* @iigindesign
