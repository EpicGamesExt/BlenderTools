# Supported Extensions
These extensions ship with the Send to Unreal addon and are supported by this repository.

## Affixes
The Affixes extension provides a convenient way to enforce prefix or postfix naming conventions on
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
`Export` collection when the Send to Unreal operation runs.

#### Automatically remove affixes after export
If true, this will automatically remove the affixes (prefix/suffix) by renaming all assets that are currently in the
`Export` collection after the Send to Unreal operation runs.


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

## Object Origin
Lets the user use the object origin, or first frame on an action as the asset origin in unreal.

### Properties
#### Use object origin
When active, this option will center each object or action at world origin before it is exported,
then it will move each object back to its original position.

### UI
The settings can be found under the `Export` tab

## Combine Meshes
Lets the user combine child meshes.

#### Static Meshes
All child meshes under an empty will be combined into one static mesh using the name of the empty.
![1](./images/extensions/combine-meshes/1.png)

In this example the name of the combine static mesh in unreal would be `CombinedCubes`

#### Skeletal Meshes
All child meshes under an armature will be combined into one skeletal mesh using the name of the first child mesh.
::: tip Note
 This might not give you enough control over the skeletal mesh name, so using the collection as parent option can be useful.
:::
![2](./images/extensions/combine-meshes/2.png)

In this example the name of the combine skeletal mesh in unreal would be `SK_Mannequin_Female`


### Properties
#### Combine child meshes
This combines all child meshes of an empty object or armature object into a single mesh when exported.

### UI
The settings can be found under the `Export` tab
