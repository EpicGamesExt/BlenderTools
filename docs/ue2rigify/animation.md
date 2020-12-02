---
layout: default
---

# Animation

<iframe src="https://www.youtube.com/embed/r3ORukeV_70" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

Let's talk about the animation workflow with ‘UE to Rigify’. When you have an animation on your ‘Source’ rig and you click ‘Convert’ and switch to ‘Control’ mode, a new Rigify rig is being created and the key frames from your original source rig are being copied over into a new action on that rig.


So let's take a look at this current action on this ‘Source’ rig called ‘run’.

![1]( {{ '/assets/images/ue2rigify/animation/1.jpg' | relative_url }} )

When I hit ‘Convert’. It converts that action over to the Rigify rig.

![2]( {{ '/assets/images/ue2rigify/animation/2.jpg' | relative_url }} )

NOTE:
‘UE to Rigify’ renames the original action to have ‘SOURCE_’ in front of it. It prefixes every action from the ‘Source’ rig so it does not overwrite any bone animations just in case the Rigify ‘Control’ rig and the ‘Source’ rig happen to have matching bone names.

Let's talk about freezing your rig. You'll see this lock icon up by your ‘Source’ rig picker.

![3]( {{ '/assets/images/ue2rigify/animation/3.jpg' | relative_url }} )

If you select this, this will freeze your rig and prevent any changes from happening to the rig. Unfreezing will allow you to make mode changes again. 

![4]( {{ '/assets/images/ue2rigify/animation/4.jpg' | relative_url }} )

NOTE:
Ultimately, what 'UE to Rigify' is doing under the hood is deleting and re-creating your entire rig every time you switch modes. Therefore once you have built your templates and are satisfied with the bones and the mappings that you have created, it is highly recommended that you freeze your rig before you start animating.

![5]( {{ '/assets/images/ue2rigify/animation/5.jpg' | relative_url }} )

Then I would click ‘Bake’, and confirm.

![6]( {{ '/assets/images/ue2rigify/animation/6.jpg' | relative_url }} )

Now we're back to our ‘Source’ rig. But now our ‘Source’ rig has the new animation on our original bones. Now the modified rig can be exported to an fbx file!