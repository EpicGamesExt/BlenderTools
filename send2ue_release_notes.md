## Minor Changes
* Fixed combine meshes extension so that all collisions associated with a child mesh get selected before export
  * [#486](https://github.com/EpicGames/BlenderTools/issues/352)
* added env `RPC_EXECUTION_HISTORY_FILE` that lets you specify a file path to write out the python execution history of the rpc module. This is useful for debugging.

## Documentation Changes
* Updated [testing docs](https://epicgames.github.io/BlenderTools/contributing/testing.html#environment-variables) to include the new env `RPC_EXECUTION_HISTORY_FILE`

## Tests Passing On
* Blender `3.1`, `3.2`
* Unreal `5.0.1`, `5.0.3`

## Special Thanks
* @iigindesign
