---
layout: default
folder: ""
---

# Preferences

The settings for ‘Send to Unreal’ are located under the addon preferences. Go to Edit > Preferences > Addons. For the category Choose ‘Pipeline’.

![1](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/preferences/1.png)

**Always use unreal scene scale:**

On a file load, sets Blender’s scene scale to 0.01 unit scale, and scales the camera clipping plane, and viewport grid accordingly. To learn more about this view the section on [scene scale](./Scene-Scale).

![9](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/scene_scale/9.png)

There you can find the ‘Send to Unreal’ addon. You'll see this preferences section, and it will have several sections in it: ‘Paths’, ‘Export’, ‘Import’, and ‘Validations’.

![2](https://blender-tools-documentation.s3.amazonaws.com/send-to-unreal/images/preferences/2.png)

* [Paths](./paths)
* [Export](./export)
* [Import](./import)
* [Validations](./validations)

One thing to note is that the settings that you modify here will persist across blender sessions. So whether you close blender or you open a new file, the settings will remain at their current values. If you save your blender file, then the current settings data gets written into the .blend file. When that .blend file is loaded again, it loads in whatever settings were saved in the .blend file.

NOTE:

The addon preferences will be reset to their default values when the addon is deactivated and reactivated.