# Affixes

The Affixes extension provides a convenient way to enforce prefix or postfix naming conventions on
assets of a particular type.  Currently, supported asset types are:
* `Static Mesh`
* `Skeletal Mesh`
* `Animation Sequence`
* `Material`
* `Texture`

## Properties
### Automatically add affixes on export
If true, this will automatically add the affixes (prefix/suffix) by renaming all assets that are currently in the
`Export` collection when the Send to Unreal operation runs.

### Automatically remove affixes after export
If true, this will automatically remove the affixes (prefix/suffix) by renaming all assets that are currently in the
`Export` collection after the Send to Unreal operation runs.


::: tip Note
 This will rename the objects in Blender, like Meshes, Textures, Materials and Actions. Be aware that this will also rename the texture image files on your hard-disk.
:::

## UI
The settings can be found under the `Export` tab


## Utility Operators
### Add Asset Affixes
Adds the affixes (prefix/suffix) by renaming all assets that are currently in the `Export` collection.

### Removes Asset Affixes
Removes the affixes (prefix/suffix) by renaming all assets that are currently in the `Export` collection.
