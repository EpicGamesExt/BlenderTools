# New Template Example
### Video:
[![](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/videos/thumbnails/new_template_example.png?)](https://www.youtube.com/watch?v=F9cTXzO8wq0&list=PLZlv_N0_O1gaxZDBH0-8A_C3OyhyLsJcE&index=4)

### Text:
Now that we understand a bit about templates and modes, let's walk through creating our own template.

So the first thing you need to do when you want to create a new template is go over here to the templates drop down, then select ‘create new’.

![1](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/new_template_example/1.png)

I'm just going to select the basic human as my starter template, and call this new template ‘Demo’.

![2](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/new_template_example/2.png)

I'm going to click ‘Save Metarig’ and then I'm gonna click ‘Convert’ to switch to ‘Control’ mode. Here you can see our Rigify rig, but nothing is attached and the bones aren’t in the right positions.

![3](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/new_template_example/3.png)

To fix this lets switch to ‘Edit Metarig’ mode.  What we need to do is remove the bones that we don't need and set the others in the correct position. X-axis mirroring and vertex snapping is automatically turned on to make this easier.

![4](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/new_template_example/4.png)

Now I will set my bones to the correct positions(I am just doing the arms for the sake of this demo).

![5](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/new_template_example/5.png)

I'm gonna go ahead and switch over to ‘FK to Source’ mode. When I'm in this mode, I can start constraining the Rigify FK bones to the ‘Source’ bones.  I can do this by selecting the two bones that need to be linked and hit Alt+1 in the 3D viewport and select ‘Link Selected Bones’.

![6](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/new_template_example/6.png)

This creates these two nodes in the node tree of the ‘Bone Remapping Nodes’ view.

![7](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/new_template_example/7.png)

By using the X-axis mirroring feature and the correct custom bone name tokens for the left and right values, we can constrain both arms simultaneously.

![8](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/new_template_example/8.png)

We will do the same thing in ‘Source to Deform’ mode.

![9](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/new_template_example/9.png)

Now if I switch to ‘Control’ mode, you can see that we have our arms and their animation copied over. You can see that are rig doesn't match up entirely because we only did the arms. But it's the exact same process to map the rest of the skeleton.

![10](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/new_template_example/10.png)

We can even go back to metarig mode and change the Rigify bone types from ‘limbs.super_limb’ to ‘limbs.simple_tenticle’ and adjust the mappings to switch the arm chain to a tentacle chain.

![11](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/new_template_example/11.png)

Now you can see the tentacle controls in ‘Control Mode’.

![12](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/new_template_example/12.png)

This is essentially the process that you have to go through to create your own templates for your own unique rigs.

