# FAQ

### Could not find an open Unreal Editor instance!
Toggle `remote execution` off and back on in your project settings.

Make sure the Multicast Bind Address in the unreal project is set to `127.0.0.1`.

Go through the quickstart again. If that doesn't work the issue is most likely due to a
networking issue. Check your systems firewall for blender and python. Also check the ports `6766` and `9998` on your
computer to see if they are blocked by another application.

Before you start the Unreal Editor, run these commands from a PowerShell prompt:

```commandline
    netstat -an|sls 6766
```

Then start your project (that has Remote Execution enabled with the multicast group endpoint presumably set to
239.0.0.1:6766) and run these commands again.

The first time, you run `netstat`, nothing should show up. The second time you run it, you should see this:

```commandline
   UDP    0.0.0.0:6766           *:*
```



### Can I have multiple Unreal editors open at once and use Send to Unreal?
Currently, no. Send to Unreal connects to the first Unreal editor process on your OS. So there isn't a good way of
specifying which Unreal editor instance to connect to at the moment. There are plans to support this is the future
though.


### Are my settings saved?
Yes, the state of the tool's properties get tracked in each blend file and saved along with the rest of the
blend file scene data.

### Why are my settings back to their defaults?
If you open a new blend file that does not already contain Send to Unreal properties, then the settings are just
the defaults. If you load a saved file, the settings will be the values they were saved at.

### Why isn't it finding my X (skeleton, physics asset, ...)?
For setting the skeleton and physics asset in the Path setting, make sure the game isn't running in PIE. For doing anything with the addon make sure not to have PIE running.
