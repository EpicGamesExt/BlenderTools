# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
from .functions import export, utilities
from .ui import importer


class Send2Ue(bpy.types.Operator):
    """Send your assets to an open unreal editor instance"""
    bl_idname = "wm.send2ue"
    bl_label = "Send to Unreal"

    def execute(self, context):
        properties = bpy.context.preferences.addons[__package__].preferences
        export.send2ue(properties)
        return {'FINISHED'}


class ImportAsset(bpy.types.Operator, importer.ImportAsset):
    """Import a game asset"""
    bl_idname = "wm.import_asset"
    bl_label = "Import Asset"
    filename_ext = ".fbx"

    def execute(self, context):
        properties = bpy.context.preferences.addons[__package__].preferences
        utilities.import_asset(self.filepath, properties)
        return {'FINISHED'}


class NullOperator(bpy.types.Operator):
    """This is an operator that changes nothing, but it used to clear the undo stack"""
    bl_idname = "send2ue.null_operator"
    bl_label = "Null Operator"

    def execute(self, context):
        return {'FINISHED'}