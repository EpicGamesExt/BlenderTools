# Validations
Validations are optional checks that can be turned off or configured to check a particular setting before starting the
Send to Unreal operation. This way an error message can be thrown to a user that tells them to correct a detail that
has been detected as "incorrect".

### Check scene linear units
This checks the scene linear units and ensures they are set to the specified value.

### Check scene frame rate
This checks the scene time units and ensures they are set to the specified value.

### Check armatures for un-applied transforms
If an armature object has un-applied transforms (meaning location and rotation are not [0,0,0] and scale is not [1,1,1]) a message is thrown to the user.

### Check if asset has unused materials
If this option is on it looks at each material index on the object and it checks if that material is
assigned to a vertex on the mesh object. If there is a unused material, then an error message is thrown to the user.

### Check texture references
This checks the texture references and sees if they actually exist on disk.

### Check paths:
This checks the export and import paths and makes sure they are valid before preforming
the operation.

### Check project settings:
This checks whether the required unreal project settings are in place before performing
the operation.

### Check blender object names:
This checks whether the blender object names in the Export collection contain any
invalid special characters or white space. While the following special characters `'".,/.:|&!~\n\r\t@#(){}[]=;^%$\*?<>` or ` have
valid usage in Blender, they are not valid to use in asset names in Unreal.

Send2UE automatically converts any invalid characters to `_` during the export process
if this validation is turned off.

::: tip Note
  Checking the unreal paths makes a few remote calls which requires an open Unreal editor instance with remote
execution enabled.  Also, if this is disabled it can shave 1 to 5 seconds off the validation step.
:::
