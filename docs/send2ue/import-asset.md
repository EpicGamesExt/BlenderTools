---
layout: default
folder: ""
---

# Import Asset

This is an overview of how to import assets into Blender with the Asset Importer.

The Asset importer allows you to import assets then run series of operations on them to fix them.  The series of operations run on the imported asset depends on what source application you select from the drop down. A source application is the application the original file was generated in.

![1]( {{ '/assets/images/send2ue/import-asset/1.jpg' | relative_url }} )

### Unreal Engine 4:

After the selected FBX file is imported the imported action location fcurves are scaled up to a match the scene scale factor with scale of 1, the objects are applied with a scale factor of 1, the scale keyframes on the root object are removed, and the keyframe are rounded to the nearest integer based on the current frame rate.
