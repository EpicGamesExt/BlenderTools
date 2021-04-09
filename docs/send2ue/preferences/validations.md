---
layout: default
folder: ""
---

# Validations

<iframe src="https://www.youtube.com/embed/1MrE2PMDkqg" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

### Check scene units:

This checks the scene units and ensures they are set to metric, and the scene scale is 1.

### Check armatures for un-applied transforms:

If an armature object has un-applied transforms a message is thrown to the user.

### Check if asset has unused materials:

If this option is on it looks at each material index on the object and it checks if that material is assigned to a vertex on the mesh object. If there is a unused material, then an error message is thrown to the user.


### Check texture references:

If a texture referenced in an object’s material can not be found in the blend file data than a error message is thrown to the user.
