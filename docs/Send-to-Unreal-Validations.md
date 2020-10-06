# Validations
## Video:
[![](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/videos/thumbnails/validations.png)](https://www.youtube.com/watch?v=1MrE2PMDkqg&list=PLZlv_N0_O1gZfQaN9qXynWllL7bzX8H3t&index=8)

## Text:

### Check if asset has unused materials:

If this option is on it looks at each material index on the object and it checks if that material is assigned to a vertex on the mesh object. If there is a unused material, then an error message is thrown to the user.


### Check texture references:

If a texture referenced in an object’s material can not be found in the blend file data than a error message is thrown to the user.