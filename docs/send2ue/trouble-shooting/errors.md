# Errors

### Could not find an open Unreal Editor instance!
This happens when remote execution is not working with your project. To fix this go through all the steps
in the [quickstart](/introduction/quickstart) again. If that doesn't work the issue is most likely due to a
networking issue. Check your systems firewall for maya and python. Also check the port `6766` on your computer to see
if it is blocked by another application.

### You do not have a collection "Export" in your outliner. Please create it.
You will receive this error if you do not have an "Export" set in your outliner. To fix this go to
`Pipeline > Utilites > Create Pre-Defined Collections`.
