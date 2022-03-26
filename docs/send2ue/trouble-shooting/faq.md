# FAQ

### Could not find an open Unreal Editor instance!
Toggle `remote execution` off and back on in your project settings.

Go through the [quickstart](/introduction/quickstart) again. If that doesn't work the issue is most likely due to a
networking issue. Check your systems firewall for maya and python. Also check the port `6766` on your computer to see
if it is blocked by another application.

Before you start the Unreal Editor, run this from a PowerShell prompt:

     netstat -an|sls 6766

Then start your project (that has Remote Execution enabled with the multicast group endpoint presumably set to 239.0.0.1:6766) and run the command again.

The first time, you run `netstat`, nothing should show up. The second time you run it, you should see this:

    UDP    0.0.0.0:6766           *:*



### Can I have multiple Unreal editors open at once and use Send to Unreal?
Currently, no. Send to Unreal connects to the first Unreal editor process on your OS. So there isn't a good way of specifying which Unreal editor instance to connect to at the moment. There are plans to support this is the future though.


### Are my settings saved?
Yes, the state of the tool's properties tracked for each maya file and saved along with the rest of the
maya file data.

### Why are my settings back to their defaults?
If you open a new maya file that does not already contain Send to Unreal properties, then the settings are just set to
the defaults.
