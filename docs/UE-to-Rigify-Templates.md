---
layout: home
---

# Templates
### Video:
[![](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/videos/thumbnails/templates.png?)](https://www.youtube.com/watch?v=eLnZfQRR-DE&list=PLZlv_N0_O1gaxZDBH0-8A_C3OyhyLsJcE&index=3&t=0s)

### Text:
Let's talk about templates in ‘UE to Rigify’.

Using the mannequin as an example again, you can see If you hit ‘Convert’, that a Rigify ‘Control’ rig is created that drives the original ‘Source’ rig.

![1](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/templates/1.png)

This is possible because of a predefined template for the unreal mannequin character that is selected from the template dropdown. This template contains all of the relationships and the bones necessary to create this rig.

![2](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/templates/2.png)

If I wanted to create a new template, I could go over here to this template panel and I could click ‘create new’.

![3](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/templates/3.png)

You can see that it adds in one of the default Rigify meta rigs.

![4](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/templates/4.png)

So basically, how this process works is you pick one of these default Rigify meta rigs and use one as a starting point.

![5](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/templates/5.png)

You name it, and then click ‘Save Metarig’.

![6](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/templates/6.png)

Now I am back in ‘Source’ mode. If I click this delete button, I can remove this template.

![7](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/templates/7.png)

Also, you can import templates from an external file. To demonstrate this, I'm going to switch over to another file where I have another character.

![8](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/templates/8.png)

The unreal mannequin template is not gonna work with this. So I need to import the template that was made for this character. I'm gonna go over to the header menu and select Edit > Preferences > Addons > UE to Rigify. Here you can see there is an import template and export template import template.

![9](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/templates/9.png)

I'm just gonna import this template file from disk.

![10](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/templates/10.png)

Now if I click ‘Convert’. You can see that the rig is generated from this template, and it all matches up because this template has been created specifically for this character.

![11](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/templates/11.png)

Now let's say we made modifications to this character’s template and we want someone else to be able to use it. All we have to do is go to Edit > Preferences > UE to Rigify and ‘Export Template’.

![12](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/templates/12.png)

You can select which template you want to export in the side panel of the export window.

![13](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/templates/13.png)

That is how you can use templates in ‘UE to Rigify’!