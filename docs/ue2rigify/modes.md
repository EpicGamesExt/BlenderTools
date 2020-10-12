---
layout: default
---

# Modes

[![](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/videos/thumbnails/modes.png?)](https://www.youtube.com/watch?v=yDMt8FeXoe4&list=PLZlv_N0_O1gaxZDBH0-8A_C3OyhyLsJcE&index=3)


Now that we understand what templates are, let's talk about how they're created. Templates are created in ‘UE to Rigify’ using five different modes:

![1](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/modes/1.png)

These modes become available as soon as you select a ‘Source’ rig.

![2](https://blender-tools-documentation.s3.amazonaws.com/ue-to-rigify/images/modes/2.png)

NOTE:
Your ‘Source’ rig is the rig that you create in blender or the rig that you import into blender that has the skinned to mesh attached to it. The idea of ‘UE to Rigify’ is you want to drive the ‘Source’ rig with your ‘Control’ rig.


**Source Mode:**

This mode is where you can see your original source rig.


**Edit Metarig Mode:**

This mode is where you add or remove bones, edit bone positions, and edit the rigify bones types.


**FK to Source Mode:**

This mode is where you edit the nodes that constrain your FK bones to the original source bones. These node links are needed if you want to transfer the existing animation from the ‘Source’ rig to the control rig.


**FK to Source Mode:**

This mode is where you edit the nodes that constrain your original source bones to the deformation bones on your ‘Control’ rig.


**Control Mode:**

This mode is where you can control your new rig and animate.