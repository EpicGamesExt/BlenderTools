# Export
When Send to Unreal writes files, the following properties dictate what and how assets are exported.

### Export object name as root bone
If true, this uses the armature object's name in blender as the root bone name in Unreal, otherwise the first bone in
the armature hierarchy is used as the root bone in unreal.

### Use object origin
This forces the unreal asset to use the blender object origin instead of the blender scene's world origin.

## Animation Settings

### Auto stash active action
This is supposed to simplify the process of creating animation and stashing it into the object’s NLA strips.
With this option turned on you can start animating on an object and export it and not have to manually edit NLA strips.

### Export all Actions
This setting ensures that regardless of the mute values or the solo value in the time editor tracks, your clips
will get exported.

### Export custom property fcurves
When enabled, this will export any object's custom properties that are in the action fcurves

## FBX Settings
All the standard FBX export settings that are in the blender FBX addon are available in this section to be
customized.
