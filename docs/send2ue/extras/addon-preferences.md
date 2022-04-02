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

### Extensions Repo Path
Set this path to the folder that contains your Send to Unreal python extensions. All extensions in this folder
will be automatically loaded.
