# Supported Extensions
These extensions ship with the Send to Unreal addon and are supported by this repository.

## Affixes
The Affixes extension provides a convenient why to enforce prefix or postfix naming conventions on
assets of a particular type.  Currently, supported asset types are:
* `Static Mesh`
* `Skeletal Mesh`
* `Animation Sequence`
* `Material`
* `Texture`


### UI
The settings can be found under the `Export` tab

### Properties
#### Automatically add affixes on export
If true, this will automatically add the affixes (prefix/suffix) by renaming all assets that are currently in the
`Export` collection when the Send to Unreal operation is run.

#### Automatically remove affixes after export
If true, this will automatically remove the affixes (prefix/suffix) by renaming all assets that are currently in the
`Export` collection after the Send to Unreal operation is run.


::: tip Note
 This will rename the objects in Blender, like Meshes, Textures, Materials and Actions. Be aware that this will also rename the texture image files on your hard-disk.
:::


### Utility Operators
#### Add Asset Affixes
Adds the affixes (prefix/suffix) by renaming all assets that are currently in the `Export` collection.

#### Removes Asset Affixes
Removes the affixes (prefix/suffix) by renaming all assets that are currently in the `Export` collection.


## UE to Rigify
A small extension that runs a validation to ensure the user is not attempting to run the Send to Unreal operation
while the using the UE to Rigify tool in control mode.
