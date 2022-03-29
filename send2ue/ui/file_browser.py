# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper


class ImportAsset(ImportHelper):
    """
    This class subclasses the import helper to define a custom file browser for importing assets.
    """
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
        window_properties = bpy.context.window_manager.send2ue

        layout = self.layout
        row = layout.row()
        row.label(text='Source Application:')
        row = layout.row()
        row.prop(window_properties, 'source_application', text='')


class ImportTemplate(ImportHelper):
    """
    Subclasses the import helper to define a custom file browser for importing setting templates.
    """
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={"HIDDEN"},
        subtype="FILE_PATH",
        )


class ExportTemplate(ExportHelper):
    """
    Subclasses the export helper to define a custom file browser for exporting setting templates.
    """
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={"HIDDEN"},
        subtype="FILE_PATH",
        )
