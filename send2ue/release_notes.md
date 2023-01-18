## Minor Changes
* The validation "Check project settings" can be turned off in send2ue validation settings
* New validation "Check blender object names" scan object names in the Export collection for any invalid characters for unreal import; it can also be toggled off in settings
    * [#529](https://github.com/EpicGames/BlenderTools/issues/529)
* Updated RPC server security
* Now escapes local view before operation
  * [#549](https://github.com/EpicGames/BlenderTools/issues/549)

## Documentation Changes
* Updated [Validations](https://epicgames.github.io/BlenderTools/send2ue/settings/validations.html) Page to include info on the two mentioned validations
* Updated [Errors](https://epicgames.github.io/BlenderTools/send2ue/trouble-shooting/errors.html) Page for [#533](https://github.com/EpicGames/BlenderTools/issues/533)

## Tests Passing On
* Blender `3.3`, `3.4`
* Unreal `5.1`

## Special Thanks
* @iigindesign
