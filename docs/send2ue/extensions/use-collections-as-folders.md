# Use Collections as Folders
Let collections in blender persist through the send2ue operation as folders in unreal.

## Properties
### use collections as folders
When active, this uses the collection hierarchy in your scene as sub folders from the specified mesh folder in your unreal project. This setting can be used concurrently with import LODs or combine meshes.

## UI
The settings can be found under the `Paths` tab

::: warning Exclusive Usage Extension
_Use Collections as Folders_ is an **exclusive usage extension**, which means that an error will be raised if it is used in combination with another exclusive usage extension.
:::
