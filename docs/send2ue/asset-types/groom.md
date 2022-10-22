# Groom

::: warning Required UE Plugins
Make sure to have the unreal plugins "Alembic Groom Importer" and "Groom" enabled for the addon to work properly.
![3](./images/groom/3.png)
:::

The tool infers an Unreal groom asset based strictly on the content of your `Export` collection. By default, each
particle system of type 'Hair' on each mesh in the collection is exported as an individual alembic file, which is
imported to unreal as a groom asset.

![1](./images/groom/1.png)

::: tip Combining Groom Assets
To gain more control over how particle systems are exported, use the [_combine assets_](/extensions/combine-assets.html)
extension that have options such as _combine groom for each mesh_ and more.
:::

::: warning
In blender, particle systems on the same mesh must have unique names. However, particles on different meshes may share
the same name. The imported groom asset uses the name of the particle system/curves object it is sourced from. To
ensure no assets are overwritten in unreal, please give each particle system and curves object a unique name
across all meshes.

<img src="./images/groom/2.png" alt="drawing" width="200"/>
:::

## Curves Objects

Curves object type is introduced in [Blender 3.3](https://www.blender.org/download/releases/3-3/), enabling a revamped hair sculpting workflow. The send2ue addon
supports the export of a curves object into a groom asset in unreal. Make sure the curves objects that you want to
export are in the `Export` collection, along with their surface meshes. Under the hood, the addon temporarily converts
the curves object into a hair particle system on the mesh that it’s surfaced to, which would then be exported as an alembic file.

## Only Groom

By default, the groom asset will import along with the mesh asset that it is surfaced to. To run a strictly groom asset
import (meaning no other asset types will be exported from blender and imported to unreal), all import options (mesh,
animation, textures) must be turned off in your [import settings](/settings/import.html) except for `Groom`.
For Curves, make sure that their surface mesh object is also placed inside the `Export` collection.

## Binding Assets and More

The addon provides an extension called [_create psot import assets for groom_](/extensions/create-post-import-groom-assets)
to automatically create unreal assets (such as a binding asset) for the imported groom asset. See the extensions section
for more information on its usage.
