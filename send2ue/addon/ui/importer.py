# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
from bpy_extras.io_utils import ImportHelper


class ImportAsset(ImportHelper):
    """
    This class subclasses the export helper to define a custom file browser
    """
    bl_idname = "send2ue.import_asset"
    bl_label = "Import Asset"

    filter_glob: bpy.props.StringProperty(
        default="*.fbx",
        options={"HIDDEN"},
        subtype="FILE_PATH",
        )

    def draw(self, context):
        """
        This function overrides the draw method in the ImportHelper class. The draw method is the function that
        defines the user interface layout and gets updated routinely.

        :param object context: The window context.
        """
        module_name = bpy.context.window_manager.send2ue.module_name
        properties = bpy.context.preferences.addons[module_name].preferences

        layout = self.layout
        row = layout.row()
        row.label(text="Source Application:")
        row = layout.row()
        row.prop(properties, "source_application", text='')
