# Addon Preferences
These preferences can be found by going to `Edit > Preferences > Addons > Send to Unreal`

### Automatically create pre-defined collections
This automatically creates the pre-defined collection (Export).


### RPC response timeout
The amount of seconds that blender stops waiting for an unreal response after it has issued a command. This might
need to be increased if you plan on importing really large assets, where the import could be longer then the
timeout value.

::: warning
It is not recommended to set the timeout too high. The timeout is a safeguard against freezing blender and unreal
indefinitely.
:::

### RPC auth token
This is the auth token that the client uses to connect to the RPC server. A default value is generated
automatically when the addon is registered. If this value is modified, Unreal must be restarted for
the change to take effect. If you want to use a static auth token, then you can set the environment
variable `RPC_AUTH_TOKEN` on your system. The addon must be uninstalled and both blender and unreal restarted and the
addon re-installed for this change to take effect.

### Extensions Repo Path
Set this path to the folder that contains your Send to Unreal python extensions. All extensions in this folder
will be automatically loaded.
