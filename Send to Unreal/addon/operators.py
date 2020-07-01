# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
from .functions import export, utilities


class Send2Ue(bpy.types.Operator):
    """Send your assets to an open unreal editor instance"""
    bl_idname = "wm.send2ue"
    bl_label = "Send to Unreal"

    def execute(self, context):
        properties = bpy.context.preferences.addons[__package__].preferences
        export.send2ue(properties)
        return {'FINISHED'}


class SetupProject(bpy.types.Operator):
    """Set your projects settings for the send to unreal tool"""
    bl_idname = "wm.setup_project"
    bl_label = "Set Project Settings to Unreal"

    def execute(self, context):
        utilities.setup_project()
        return {'FINISHED'}


class SetSceneScale(bpy.types.Operator):
    """Set your current scene scale to 0.01, scale up, and then apply scale"""
    bl_idname = "wm.set_scene_scale"
    bl_label = "Send to Unreal: Scene Scale Warning"

    message: bpy.props.StringProperty(default="")
    confirm_message: bpy.props.StringProperty(default="")
    fix: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        properties = bpy.context.preferences.addons[__package__].preferences
        if self.fix:
            utilities.set_unreal_scene_scale(properties)

            # get the current scene scale
            scene_scale = bpy.context.scene.unit_settings.scale_length

            # scale up and apply all object scale to account for the scene scale change
            utilities.scale_all_objects_and_apply_transforms(scene_scale / properties.unreal_unit_scale)
        else:
            bpy.ops.wm.url_open(url="https://github.com/EpicGames/BlenderTools/wiki/Send-to-Unreal-Scene-Scale")
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=600)

    def draw(self, context):
        properties = bpy.context.preferences.addons[__package__].preferences
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.label(text='Importing this skeleton to Unreal might cause issues!', icon='ERROR')
        row = box.row()
        row.label(text=self.message)

        if self.confirm_message:
            row = box.row()
            row.label(text=self.confirm_message)

        row = box.row()
        row.prop(properties, 'do_not_show_again', text='Do not show again')