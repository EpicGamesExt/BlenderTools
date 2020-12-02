---
layout: default
---

# Templates

<iframe src="https://www.youtube.com/embed/eLnZfQRR-DE" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>


Let's talk about templates in ‘UE to Rigify’.

Using the mannequin as an example again, you can see If you hit ‘Convert’, that a Rigify ‘Control’ rig is created that drives the original ‘Source’ rig.

![1]( {{ '/assets/images/ue2rigify/templates/1.jpg' | relative_url }} )

This is possible because of a predefined template for the unreal mannequin character that is selected from the template dropdown. This template contains all of the relationships and the bones necessary to create this rig.

![2]( {{ '/assets/images/ue2rigify/templates/2.jpg' | relative_url }} )

If I wanted to create a new template, I could go over here to this template panel and I could click ‘create new’.

![3]( {{ '/assets/images/ue2rigify/templates/3.jpg' | relative_url }} )

You can see that it adds in one of the default Rigify meta rigs.

![4]( {{ '/assets/images/ue2rigify/templates/4.jpg' | relative_url }} )

So basically, how this process works is you pick one of these default Rigify meta rigs and use one as a starting point.

![5]( {{ '/assets/images/ue2rigify/templates/5.jpg' | relative_url }} )

You name it, and then click ‘Save Metarig’.

![6]( {{ '/assets/images/ue2rigify/templates/6.jpg' | relative_url }} )

Now I am back in ‘Source’ mode. If I click this delete button, I can remove this template.

![7]( {{ '/assets/images/ue2rigify/templates/7.jpg' | relative_url }} )

Also, you can import templates from an external file. To demonstrate this, I'm going to switch over to another file where I have another character.

![8]( {{ '/assets/images/ue2rigify/templates/8.jpg' | relative_url }} )

The unreal mannequin template is not gonna work with this. So I need to import the template that was made for this character. I'm gonna go over to the header menu and select Edit > Preferences > Addons > UE to Rigify. Here you can see there is an import template and export template import template.

![9]( {{ '/assets/images/ue2rigify/templates/9.jpg' | relative_url }} )

I'm just gonna import this template file from disk.

![10]( {{ '/assets/images/ue2rigify/templates/10.jpg' | relative_url }} )

Now if I click ‘Convert’. You can see that the rig is generated from this template, and it all matches up because this template has been created specifically for this character.

![11]( {{ '/assets/images/ue2rigify/templates/11.jpg' | relative_url }} )

Now let's say we made modifications to this character’s template and we want someone else to be able to use it. All we have to do is go to Edit > Preferences > UE to Rigify and ‘Export Template’.

![12]( {{ '/assets/images/ue2rigify/templates/12.jpg' | relative_url }} )

You can select which template you want to export in the side panel of the export window.

![13]( {{ '/assets/images/ue2rigify/templates/13.jpg' | relative_url }} )

That is how you can use templates in ‘UE to Rigify’!