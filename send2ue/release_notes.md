## Minor Changes
* Fixed various connection and timeout issues by removing the authorization token in favor of checking CORS.
  * [563](https://github.com/EpicGames/BlenderTools/issues/563)
  * [564](https://github.com/EpicGames/BlenderTools/issues/564)
  * [552](https://github.com/EpicGames/BlenderTools/issues/552)
* Fixed issue with FBX exporter failing to export with warnings. Now the exports finish and warnings are printed to the system console.
  * [565](https://github.com/EpicGames/BlenderTools/issues/565)

## Deprecated
* The `RPC Auth Token` option has been removed from the addon preferences since it can be cumbersome to configure and
was causing issues. Instead, the same security can be provided by checking CORS in the RPC server.

## Tests Passing On
* Blender `3.3`, `3.4`
* Unreal `5.1`
