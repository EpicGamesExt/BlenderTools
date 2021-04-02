---
layout: default
folder: ""
---

# Paths
<iframe src="https://www.youtube.com/embed/oVIKQVbXgbY" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>



First, let's talk about the settings under the ‘Paths’ section. You'll see that there is this drop down, and it gives you three options: ‘Send to Unreal’, ‘Export to Disk’ or ‘Both’.

![1]( {{ '/assets/images/send2ue/preferences/paths/1.jpg' | relative_url }} )

When using ‘Send to Unreal’ the paths are the relative paths from your open Unreal project that ‘Send to Unreal’ uses when it runs the import. The ‘Game’ folder is equivalent to the ‘Content’ folder you see in your open Unreal project.

![2]( {{ '/assets/images/send2ue/preferences/paths/2.jpg' | relative_url }} )
![3]( {{ '/assets/images/send2ue/preferences/paths/3.jpg' | relative_url }} )

When using ‘Export to Disk’, the path is the full path to the folder where the files will be exported on disk.

![4]( {{ '/assets/images/send2ue/preferences/paths/4.jpg' | relative_url }} )
![5]( {{ '/assets/images/send2ue/preferences/paths/5.jpg' | relative_url }} )

When using ‘Both’, it will export to the specified folders on disk and import to the specified folders in your project.

### Use immediate parent collection name:

This makes the immediate parent collection the name of the asset.

### Use collections as folders:

This uses the collection hierarchy in your scene as sub folders from the specified mesh folder in your unreal project.

### Mesh Folder (Unreal):

This is the mesh import path. All your static and skeletal meshes will be imported to this location in your open unreal project.


### Animation Folder (Unreal):

This is the animation import path. All your actions that are in an Armature object’s NLA strips will be imported to this location in your open Unreal Project.


### Skeleton Asset (Unreal):

This is the direct path to the Skeleton you want to import animation on. You can get this path by right-clicking on the skeleton asset in Unreal and selecting ‘Copy Reference’.

![6]( {{ '/assets/images/send2ue/preferences/paths/6.jpg' | relative_url }} )

NOTE:

Animation only imports can also be done by leaving the Skeleton Asset path blank and having only a rig under the ‘Rig’ collection.  In this case, ‘Send to Unreal’ will try to import onto a Skeleton in the folder specified by ‘Mesh Folder (Unreal)’ that matches the name of the skeletal mesh plus ‘_Skeleton’.

### Mesh Folder (Disk):

This is the path to the folder where your mesh is exported to on disk. All your static and skeletal meshes will be exported to this location. The file names will match the object names in Blender.


### Animation Folder (Disk):

This is the path to the folder where your actions will be exported to on disk. All your actions that are in an Armature object’s NLA strips will be exported to this location. The file names will match the action names in Blender.
