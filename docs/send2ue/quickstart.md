---
layout: default
folder: ""
---

# Quickstart
:
<iframe width="560" height="315" src="https://www.youtube.com/embed/apa9EXI2KZA" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>


This quick start guide will help you get up and running with the Send to Unreal addon.

First thing you need to do is open Blender. You need to install the add on. Go to Edit > Preferences then to addons. Click ‘install’.

![1](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/quickstart/1.png?)

Go to the location where you have your addon on disk and install the zip file. Once installed. Go ahead and activate it.

![2](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/quickstart/2.png?)

You'll notice when you activate it. This pipeline menu gets built.

![3](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/quickstart/3.png?)

Also, as soon as you interact with the scene, you will see that these collections get created. These collections are important for sending objects over to Unreal.

![4](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/quickstart/4.png?)

Next thing you want to do is configure your Unreal project. So open up on Unreal and create a new project. Once your project is open, go to Edit >Plugins.

![5](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/quickstart/5.png?)

Search for the Python Editor Script Plugin and enable it. Then search for the Editor Scripting Utilities Plugin and enable it.

![6](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/quickstart/6.png?)

Once you have enabled the plugins, you'll be prompted to restart the editor. Go ahead and restart. Once you've restarted, go to Edit > Project Settings.

![7](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/quickstart/7.png?)

Search for ‘python’ and then enable remote execution. Now Send to Unreal will work with your new Unreal project.

![8](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/quickstart/8.png?)

Another thing I like to do is go to Edit > Editor Preferences.

![9](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/quickstart/9.png?)

Search for ‘CPU’, then under Editor Performance disable ‘Use Less CPU when in Background’.  That way unreal continues to update even when it is not the active application. Now the Blender and Unreal UI will update at the same time and you will see your changes update without having to click on Unreal.

![10](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/quickstart/10.png?)

A simple test we can do in Blender to make sure this is working is move our cube to our mesh collection.

![11](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/quickstart/11.png?)

Click Pipeline>Export>Send to Unreal.

![12](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/quickstart/12.png?)

NOTE: on windows, if you see this security alert, go ahead and allow Blender access across your private network.

![13](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/quickstart/13.png?)

You should now see the cube in unreal under untitled category > untitled asset > Cube.

![14](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/quickstart/14.png?)

As you can see, Send to Unreal is now working!