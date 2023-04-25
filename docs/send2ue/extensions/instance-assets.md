# Instance Assets
Spawns the imported assets as actors in the active unreal level with a location that matches the world location of
the object in the blender scene.

## Properties
### Place in active level
Spawns assets in the active level at the same location they are positioned in the blender scene.

This is only supported for the following asset types:
* `StaticMesh`
* `SkeletalMesh`
* `AnimSequence`

### Use mesh instances
Instances static and skeletal meshes in the active level. If the data on an object is linked it will not be
re-imported, just instanced. Note that this will force the asset to take on the name of its mesh data,
rather than its object name, and the actors in the unreal level will match the blender object name.

### UI
The settings can be found under the `Import` tab
