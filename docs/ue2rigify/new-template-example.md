---
layout: default
---

# New Template Example

<iframe src="https://www.youtube.com/embed/F9cTXzO8wq0" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>


Now that we understand a bit about templates and modes, let's walk through creating our own template.

So the first thing you need to do when you want to create a new template is go over here to the templates drop down, then select ‘create new’.

![1]( {{ '/assets/images/ue2rigify/new-template-example/1.jpg' | relative_url }} )

I'm just going to select the basic human as my starter template, and call this new template ‘Demo’.

![2]( {{ '/assets/images/ue2rigify/new-template-example/2.jpg' | relative_url }} )

I'm going to click ‘Save Metarig’ and then I'm gonna click ‘Convert’ to switch to ‘Control’ mode. Here you can see our Rigify rig, but nothing is attached and the bones aren’t in the right positions.

![3]( {{ '/assets/images/ue2rigify/new-template-example/3.jpg' | relative_url }} )

To fix this lets switch to ‘Edit Metarig’ mode.  What we need to do is remove the bones that we don't need and set the others in the correct position. X-axis mirroring and vertex snapping is automatically turned on to make this easier.

![4]( {{ '/assets/images/ue2rigify/new-template-example/4.jpg' | relative_url }} )

Now I will set my bones to the correct positions(I am just doing the arms for the sake of this demo).

![5]( {{ '/assets/images/ue2rigify/new-template-example/5.jpg' | relative_url }} )

I'm gonna go ahead and switch over to ‘FK to Source’ mode. When I'm in this mode, I can start constraining the Rigify FK bones to the ‘Source’ bones.  I can do this by selecting the two bones that need to be linked and hit Alt+1 in the 3D viewport and select ‘Link Selected Bones’.

![6]( {{ '/assets/images/ue2rigify/new-template-example/6.jpg' | relative_url }} )

This creates these two nodes in the node tree of the ‘Bone Remapping Nodes’ view.

![7]( {{ '/assets/images/ue2rigify/new-template-example/7.jpg' | relative_url }} )

By using the X-axis mirroring feature and the correct custom bone name tokens for the left and right values, we can constrain both arms simultaneously.

![8]( {{ '/assets/images/ue2rigify/new-template-example/8.jpg' | relative_url }} )

We will do the same thing in ‘Source to Deform’ mode.

![9]( {{ '/assets/images/ue2rigify/new-template-example/9.jpg' | relative_url }} )

Now if I switch to ‘Control’ mode, you can see that we have our arms and their animation copied over. You can see that are rig doesn't match up entirely because we only did the arms. But it's the exact same process to map the rest of the skeleton.

![10]( {{ '/assets/images/ue2rigify/new-template-example/10.jpg' | relative_url }} )

We can even go back to metarig mode and change the Rigify bone types from ‘limbs.super_limb’ to ‘limbs.simple_tenticle’ and adjust the mappings to switch the arm chain to a tentacle chain.

![11]( {{ '/assets/images/ue2rigify/new-template-example/11.jpg' | relative_url }} )

Now you can see the tentacle controls in ‘Control Mode’.

![12]( {{ '/assets/images/ue2rigify/new-template-example/12.jpg' | relative_url }} )

Transferring root motion is also possible by using the source rig object node. A link can be made between it and the 
desired bone in 'FK to Source' mode and 'Source to Deform' mode. The source rig object node can be added to the node tree 
by hitting:

SHIFT+A > Object > Source Rig Object

![13]( {{ '/assets/images/ue2rigify/new-template-example/13.jpg' | relative_url }} )
![14]( {{ '/assets/images/ue2rigify/new-template-example/14.jpg' | relative_url }} )

This is essentially the process that you have to go through to create your own templates for your own unique rigs.