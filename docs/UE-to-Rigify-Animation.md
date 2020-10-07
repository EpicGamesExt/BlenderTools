---
layout: home
---

# Animation
### Video:
[![](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/videos/thumbnails/animation.png?)](https://www.youtube.com/watch?v=r3ORukeV_70&list=PLZlv_N0_O1gaxZDBH0-8A_C3OyhyLsJcE&index=5)

### Text:
Let's talk about the animation workflow with ‘UE to Rigify’. When you have an animation on your ‘Source’ rig and you click ‘Convert’ and switch to ‘Control’ mode, a new Rigify rig is being created and the key frames from your original source rig are being copied over into a new action on that rig.


So let's take a look at this current action on this ‘Source’ rig called ‘run’.

![1](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/animation/1.png)

When I hit ‘Convert’. It converts that action over to the Rigify rig.

![2](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/animation/2.png)

NOTE:
‘UE to Rigify’ renames the original action to have ‘SOURCE_’ in front of it. It prefixes every action from the ‘Source’ rig so it does not overwrite any bone animations just in case the Rigify ‘Control’ rig and the ‘Source’ rig happen to have matching bone names.

Let's talk about freezing your rig. You'll see this lock icon up by your ‘Source’ rig picker.

![3](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/animation/3.png)

If you select this, this will freeze your rig and prevent any changes from happening to the rig.

![4](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/animation/4.png)

NOTE:
Once you have built your templates and you're satisfied with the bones and the mappings that you have created and you want to start animating, you need to freeze your rig! This is a necessary step. If you want to animate on your rig, this will ensure that no data gets lost on a file save or file load, or if you switch back and forth between modes. Ultimately, what ‘UE to Rigify’ is doing under the hood is deleting and re-creating your entire rig every time you switch modes. Therefore, if you add any information on the bones, that information will be lost when the mode changes. So this lock icon ensures the modes will not change.

Now let's say I create an animation on my ‘Control’ rig and want to bake those changes into my ‘Source’ rig. First I would unlock my rig, and confirm that I want to do this.

![5](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/animation/5.png)

Then I would click ‘Bake’, and confirm.

![6](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/animation/6.png)

Now we're back to our ‘Source’ rig. But now our ‘Source’ rig has the new animation on our original bones. Now the modified rig can be exported to an fbx file!