# Errors

### Could not find an open Unreal Editor instance!
This happens when remote execution is not working with your project. To fix this go through all the steps
in the [quickstart](/introduction/quickstart) again. If that doesn't work the issue is most likely due to a
networking issue. Check your systems firewall for maya and python. Also check the port `6766` on your computer to see
if it is blocked by another application.

### You do not have a set "Export" in your outliner. Please create it.
You will receive this error if you do not have an "Export" set in your outliner. To fix this go to
`Pipeline > Tools > Send to Unreal > Create Sets`.

### Node `node` has an invalid name. Please rename it.


### The linear unit `label` is not recommended. Please change to `validation_label`, or disable this validation.


### The time unit `label` is not recommended. Please change to `validation_label`, or disable this validation.

### The up axis `label` is not recommended. Please change to `validation_label`, or disable this validation.

### You do not have the correct objects under the "Export" set, or your rig does not have any animation to export!'

### You do not have any set under the "Export" set to match a track name

### Please specify a folder in your unreal project where your asset will be imported.

### Please specify at least a root folder location.

### The root folder `root_folder` does not exist in your unreal project.

### Relative paths can only be used if this file is saved.

### The specified folder `file_path` does not exist on disk.

### The permissions of `file_path` will not allow files to write to it.

### There is no specified sequence in the "Paths" section of your settings.

### The track `track_name` does not exist the sequence `asset_path`. Please ensure the set name under the "Export" set matches a track name.

### `root_joint` needs its unreal skeleton asset path specified under the "Path" settings, so it can be imported correctly!

### Mesh `mesh` has a lambert1 material please assign it another material, or disable this validation.

### `mesh` does not follow the correct lod naming convention defined in the import setting by the lod regex.

### `mesh` has a missing texture reference `texture_file`.

### Joint `root_joint` has a orientation of {orientation}. It must be (0,0,0) to continue, or disable this validation.

### Joint `root_joint` has a scale orientation of {scale_orientation}. It must be (0,0,0) to continue, or disable this validation.
