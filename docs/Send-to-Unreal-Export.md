---
layout: home
---

# Export
## Video:
[![](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/videos/thumbnails/export.png)](https://www.youtube.com/watch?v=yZz5Zl5EB4A&list=PLZlv_N0_O1gZfQaN9qXynWllL7bzX8H3t&index=6)

## Text:
Let's take a look at the export settings. If you look under the export settings, you'll see a series of options. All these options are operations that will get applied to your objects before they're exported to a FBX file.

![1](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/export/1.png?)


### Automatically scale bones:

This automatically scales your armature objects so they import at scale of 1


### Export all actions:

This setting ensures that regardless of the mute values on your NLA tracks, your actions will get exported. It does this by un-muting all NLA tracks before the FBX export.


### Auto stash active action:

This is supposed to simplify the process of creating animation and stashing it into the object’s NLA strips.  With this option turned on you can start animating on an object and export it and not have to manually edit NLA strips.


NOTE:
If you are manually editing NLA strips as part of your workflow, it is recommended that you turn this off so that the automatic stashing of the active action does not modify your NLA track setup.


### Auto sync control NLA strips to source:

When using ‘UE to Rigify’ with this option turned on, ‘Send to Unreal’ will remove the NLA strips from the source rig, then copy over the strips from the control rig to the source rig.  The values copied over are: nla track name, nla track mute value, strip name, strip start frame, strip end frame, and strip scale.


NOTE:

This option will be greyed out if ‘UE to Rigify’ is not installed and activated.  Also, if you turn this option off because you want to manually edit the source rig’s NLA strips differently than the control rig’s NLA strips, then it is recommended that you turn off ‘Export all actions’ as well.’


### Use object origin:

When active, this option will center each object at world origin before it is exported to an FBX, then it will move each object back to its original position.


### FBX Settings:

All the standard FBX export settings that are in the normal blender fbx export. The only settings missing are: exporting by selection or by a collection and exporting all of your actions versus exporting just actions in an object NLA strip. Also you can’t change which object types can be exported. (only types ‘Empty’, ‘Armature’, and ‘Mesh’ are supported).