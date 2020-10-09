---
layout: default
folder: ""
---

# NLA Strips
:
[![](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/videos/thumbnails/nla_tracks.png?)](https://www.youtube.com/watch?v=l0dVg7Oulq8&list=PLZlv_N0_O1gZfQaN9qXynWllL7bzX8H3t&index=4)



Send to Unreal uses NLA strips to associate particular actions with particular objects. Understanding this relationship is essential to exporting your actions correctly. Let's look at an example with the Mannequin that has the ThirdPersonRun animation on it. 

![1](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/nla_strips/1.png)

If we exported this to an FBX file with just the default animation settings we would get something like this when we import to Unreal. Which is not what we want.

![2](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/nla_strips/2.png)

Send to Unreal does not use the default FBX export options that export all actions in a scene, instead, it only exports actions in NLA strips.

![3](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/nla_strips/3.png)

This way we get this.

![4](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/nla_strips/4.png)

In order for this to work correctly, you need to have your actions underneath a NLA Track on your object. For example, you can see right now that our third person run action is actually a strip in a NLA track and it is un-muted, and it's underneath our mannequin’s rig object ‘root’.

![5](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/nla_strips/5.png)

If you want to export multiple actions on a single object, simply add the action to the object’s NLA stack.

![6](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/nla_strips/6.png)

NOTE: By default, ‘Send to Unreal’ automatically pushes your active action into the NLA stack if it doesn’t already exist in the stack.

One important thing to note is that the length of your in NLA strips determines the length of your animation in Unreal.

![7](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/nla_strips/7.png)

Also, the scale of your NLA tracks determines the speed of your action in Unreal.

![8](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/nla_strips/8.png)

That summarizes how NLA strips work with ‘Send to Unreal’.