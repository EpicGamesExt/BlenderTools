---
layout: default
---

# Collections
## Video:
[![](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/videos/thumbnails/collections.png?)](https://www.youtube.com/watch?v=CukIe_OSGiQ&list=PLZlv_N0_O1gZfQaN9qXynWllL7bzX8H3t&index=3)

## Text:

Send to Unreal creates several collections for you. These collections are important, and each name is a reserved name for Send to Unreal. The exact names are: ‘Mesh’, ‘Rig’, ‘Extras’.

The ‘Mesh’ collection is for all objects of type mesh. The ‘Rig’ collection is for all objects of type armature and the ‘Extras’ collection is used to organize and hide a lot of information and objects that are not important to the user.

![1](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/collections/1.png)

For example, you can see here that I have the mannequin character in Blender.

![2](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/collections/2.png)

I will move just the mannequin mesh object to the mesh collection.

![3](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/collections/3.png)

When I click ‘Send to Unreal’, a static mesh is imported to the engine. This is because we have just a mesh under the ‘Mesh’ collection, but we do not have an armature object under the ‘Rig’ collection.

![4](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/collections/4.png)

This time I'm gonna move the mannequin bones over to the ‘Rig’ collection. I'm gonna perform that same and just click ‘Send to Unreal’.

![5](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/collections/5.png)

This time you can see Unreal imports a skeletal mesh. It knows that the exported object is a skeletal mesh because the mannequin mesh is under the ‘Mesh’ collection and and the Mannequin armature object is under the ‘Rig’ collection. Also since this mannequin mesh is a child of the mannequin rig, it is imported as a skeletal mesh in Unreal. When exporting meshes, it takes the name of the object in Blender, and that is the name that is given to the asset in Unreal. The skeleton is also given the name of the mesh object it is attached to along with ‘_Skeleton’ appended to the name.

![6](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/collections/6.png)

Also, we can see that our animation has been imported as well.

![7](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/collections/7.png)


The name of the imported animation will match the name of the action in Blender. If you want to import only animation, just move the mesh object outside of the ‘Mesh’ collection, so that there is only the mannequin rig with its bones and animation data under the ‘Rig’ collection. When you click ‘Send to Unreal’ only the animation will be imported.


Note: This will also significantly improve your iteration times if you are just editing animation because Send to Unreal doesn’t have to re-import the mesh data as well.

![8](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/collections/8.png)

This summarizes how Send to Unreal uses these collection names.