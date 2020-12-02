---
layout: default
folder: ""
---

# Quickstart

<iframe src="https://www.youtube.com/embed/apa9EXI2KZA" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>


This quick start guide will help you get up and running with the Send to Unreal addon.

First thing you need to do is open Blender. You need to install the add on. Go to Edit > Preferences then to addons. Click ‘install’.

![1]( {{ '/assets/images/send2ue/quickstart/1.jpg' | relative_url }} )

Go to the location where you have your addon on disk and install the zip file. Once installed. Go ahead and activate it.

![2]( {{ '/assets/images/send2ue/quickstart/2.jpg' | relative_url }} )

You'll notice when you activate it. This pipeline menu gets built.

![3]( {{ '/assets/images/send2ue/quickstart/3.jpg' | relative_url }} )

Also, as soon as you interact with the scene, you will see that these collections get created. These collections are important for sending objects over to Unreal.

![4]( {{ '/assets/images/send2ue/quickstart/4.jpg' | relative_url }} )

Next thing you want to do is configure your Unreal project. So open up on Unreal and create a new project. Once your project is open, go to Edit >Plugins.

![5]( {{ '/assets/images/send2ue/quickstart/5.jpg' | relative_url }} )

Search for the Python Editor Script Plugin and enable it. Then search for the Editor Scripting Utilities Plugin and enable it.

![6]( {{ '/assets/images/send2ue/quickstart/6.jpg' | relative_url }} )

Once you have enabled the plugins, you'll be prompted to restart the editor. Go ahead and restart. Once you've restarted, go to Edit > Project Settings.

![7]( {{ '/assets/images/send2ue/quickstart/7.jpg' | relative_url }} )

Search for ‘python’ and then enable remote execution. Now Send to Unreal will work with your new Unreal project.

![8]( {{ '/assets/images/send2ue/quickstart/8.jpg' | relative_url }} )

Another thing I like to do is go to Edit > Editor Preferences.

![9]( {{ '/assets/images/send2ue/quickstart/9.jpg' | relative_url }} )

Search for ‘CPU’, then under Editor Performance disable ‘Use Less CPU when in Background’.  That way unreal continues to update even when it is not the active application. Now the Blender and Unreal UI will update at the same time and you will see your changes update without having to click on Unreal.

![10]( {{ '/assets/images/send2ue/quickstart/10.jpg' | relative_url }} )

A simple test we can do in Blender to make sure this is working is move our cube to our mesh collection.

![11]( {{ '/assets/images/send2ue/quickstart/11.jpg' | relative_url }} )

Click Pipeline>Export>Send to Unreal.

![12]( {{ '/assets/images/send2ue/quickstart/12.jpg' | relative_url }} )

NOTE: on windows, if you see this security alert, go ahead and allow Blender access across your private network.

![13]( {{ '/assets/images/send2ue/quickstart/13.jpg' | relative_url }} )

You should now see the cube in unreal under untitled category > untitled asset > Cube.

![14]( {{ '/assets/images/send2ue/quickstart/14.jpg' | relative_url }} )

As you can see, Send to Unreal is now working!