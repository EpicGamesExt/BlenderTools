---
layout: default
folder: ""
---

# NLA Strips

<iframe src="https://www.youtube.com/embed/l0dVg7Oulq8" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

Send to Unreal uses NLA strips to associate particular actions with particular objects. Understanding this relationship is essential to exporting your actions correctly. Let's look at an example with the Mannequin that has the ThirdPersonRun animation on it. 

![1]( {{ '/assets/images/send2ue/nla-strips/1.jpg' | relative_url }} )

If we exported this to an FBX file with just the default animation settings we would get something like this when we import to Unreal. Which is not what we want.

![2]( {{ '/assets/images/send2ue/nla-strips/2.jpg' | relative_url }} )

Send to Unreal does not use the default FBX export options that export all actions in a scene, instead, it only exports actions in NLA strips.

![3]( {{ '/assets/images/send2ue/nla-strips/3.jpg' | relative_url }} )

This way we get this.

![4]( {{ '/assets/images/send2ue/nla-strips/4.jpg' | relative_url }} )

In order for this to work correctly, you need to have your actions underneath a NLA Track on your object. For example, you can see right now that our third person run action is actually a strip in a NLA track and it is un-muted, and it's underneath our mannequin’s rig object ‘root’.

![5]( {{ '/assets/images/send2ue/nla-strips/5.jpg' | relative_url }} )

If you want to export multiple actions on a single object, simply add the action to the object’s NLA stack.

![6]( {{ '/assets/images/send2ue/nla-strips/6.jpg' | relative_url }} )

NOTE: By default, ‘Send to Unreal’ automatically pushes your active action into the NLA stack if it doesn’t already exist in the stack.

One important thing to note is that the length of your in NLA strips determines the length of your animation in Unreal.

![7]( {{ '/assets/images/send2ue/nla-strips/7.jpg' | relative_url }} )

Also, the scale of your NLA tracks determines the speed of your action in Unreal.

![8]( {{ '/assets/images/send2ue/nla-strips/8.jpg' | relative_url }} )

That summarizes how NLA strips work with ‘Send to Unreal’.