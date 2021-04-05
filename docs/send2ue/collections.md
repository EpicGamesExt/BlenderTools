---
layout: default
folder: ""
---

# Collections
<iframe src="https://www.youtube.com/embed/CukIe_OSGiQ" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>



By default Send to Unreal creates several collections automatically for you: ‘Mesh’, ‘Rig’, ‘Collison’, ‘Extras’. It is important to note that only visible objects in these collections will be exported. 

> Note: You can disable the automatic collection creation in the addons' preferences under ´General´:
> 
> ![10]( {{ '/assets/images/send2ue/collections/10.jpg' | relative_url }} )

## Static Meshes

The ‘Mesh’ collection is for all objects of type mesh. The ‘Rig’ collection is for all objects of type armature, the 'Collison' collection is for mesh collision assets(only static meshes are supported at this time), and the ‘Extras’ collection is used to organize and hide a lot of information and objects that are not important to the user.

![1]( {{ '/assets/images/send2ue/collections/1.jpg' | relative_url }} )

For example, you can see here that I have the mannequin character in Blender.

![2]( {{ '/assets/images/send2ue/collections/2.jpg' | relative_url }} )

I will move just the mannequin mesh object to the mesh collection.

![3]( {{ '/assets/images/send2ue/collections/3.jpg' | relative_url }} )

When I click ‘Send to Unreal’, a static mesh is imported to the engine. This is because we have just a mesh under the ‘Mesh’ collection, but we do not have an armature object under the ‘Rig’ collection.

![4]( {{ '/assets/images/send2ue/collections/4.jpg' | relative_url }} )

## Skeletal Meshes

This time I'm gonna move the mannequin bones over to the ‘Rig’ collection. I'm gonna perform that same and just click ‘Send to Unreal’.

> Note: Your mesh must have an armature as a parent in order for it to import as a skeletal mesh

![5]( {{ '/assets/images/send2ue/collections/5.jpg' | relative_url }} )

As you can see Unreal imports a skeletal mesh now. It knows that the exported object is a skeletal mesh because the mannequin mesh is under the ‘Mesh’ collection and and the Mannequin armature object is under the ‘Rig’ collection. Also since this mannequin mesh is a child of the mannequin rig, it is imported as a skeletal mesh in Unreal. When exporting meshes, it takes the name of the object in Blender, and that is the name that is given to the asset in Unreal. The skeleton is also given the name of the mesh object it is attached to along with ‘_Skeleton’ appended to the name.

![6]( {{ '/assets/images/send2ue/collections/6.jpg' | relative_url }} )

Also, we can see that our animation has been imported as well.

![7]( {{ '/assets/images/send2ue/collections/7.jpg' | relative_url }} )

The name of the imported animation will match the name of the action in Blender. If you want to import only animation, just move the mesh object outside of the ‘Mesh’ collection, so that there is only the mannequin rig with its bones and animation data under the ‘Rig’ collection. When you click ‘Send to Unreal’ only the animation will be imported.

> Note: This will also significantly improve your iteration times if you are just editing animation because Send to Unreal doesn’t have to re-import the mesh data as well.

![8]( {{ '/assets/images/send2ue/collections/8.jpg' | relative_url }} )

## Custom Collision Meshes

Send to Unreal supports custom collision meshes. These meshes are merged with the exported file and not exported separately. To add a collision mesh:

1. Add a new mesh.
2. Place the mesh under the Collision collection.
3. Prefix the mesh name with `UBX_` for box collision, `UCP_` for capsule collision, `USP_` for sphere collision, or `UCX_` for convex collision.

Example: If your static mesh object is called SM_Cube, you add a new mesh object under the 'Collision' collection and name it UCX_SM_Cube:

![9]( {{ '/assets/images/send2ue/collections/9.jpg' | relative_url }} )

For details, see [FBX Static Mesh Pipeline](https://docs.unrealengine.com/en-US/WorkingWithContent/Importing/FBX/StaticMeshes/index.html#collision).

This summarizes how Send to Unreal uses these collection names.
