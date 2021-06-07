# Copyright Epic Games, Inc. All Rights Reserved.
import bpy


class TOPBAR_MT_Import(bpy.types.Menu):
    """
    This defines a new class that will be the menu, "Import".
    """
    bl_idname = "TOPBAR_MT_Import"
    bl_label = "Import"

    def draw(self, context):
        self.layout.operator('wm.import_asset')


class TOPBAR_MT_Export(bpy.types.Menu):
    """
    This defines a new class that will be the menu, "Export".
    """
    bl_idname = "TOPBAR_MT_Export"
    bl_label = "Export"

    def draw(self, context):
        self.layout.operator('wm.send2ue')
        self.layout.operator('wm.advanced_send2ue')


class TOPBAR_MT_Utilities(bpy.types.Menu):
    """
    This defines a new class that will be the menu, "Utilities".
    """
    bl_idname = "TOPBAR_MT_Utilities"
    bl_label = "Utilities"

    def draw(self, context):
        self.layout.operator('wm.add_asset_affixes')
        self.layout.operator('wm.remove_asset_affixes')
        self.layout.operator('wm.create_predefined_collections')


class TOPBAR_MT_Pipeline(bpy.types.Menu):
    """
    This defines a new class that will be the top most parent menu, "Pipeline".
    All the other action menu items are children of this.
    """
    bl_idname = "TOPBAR_MT_Pipeline"
    bl_label = "Pipeline"

    def draw(self, context):
        pass


def pipeline_menu(self, context):
    """
    This function creates the pipeline menu item. This will be referenced in other functions
    as a means of appending and removing it's contents from the top bar editor class
    definition.

    :param object self: This refers the the Menu class definition that this function will
    be appended to.
    :param object context: This parameter will take the current blender context by default,
    or can be passed an explicit context.
    """
    self.layout.menu(TOPBAR_MT_Pipeline.bl_idname)


def import_menu(self, context):
    """
    This function creates the import menu item. This will be referenced in other functions
    as a means of appending and removing it's contents from the top bar editor class
    definition.

    :param object self: This refers the the Menu class definition that this function will
    be appended to.
    :param object context: This parameter will take the current blender context by default,
    or can be passed an explicit context.
    """
    self.layout.menu(TOPBAR_MT_Import.bl_idname)


def export_menu(self, context):
    """
    This function creates the export menu item. This will be referenced in other functions
    as a means of appending and removing it's contents from the top bar editor class
    definition.

    :param object self: This refers the the Menu class definition that this function will
    be appended to.
    :param object context: This parameter will take the current blender context by default,
    or can be passed an explicit context.
    """
    self.layout.menu(TOPBAR_MT_Export.bl_idname)


def utilities_menu(self, context):
    """
    This function creates the utilities menu item. This will be referenced in other functions
    as a means of appending and removing it's contents from the top bar editor class
    definition.

    :param object self: This refers the the Menu class definition that this function will
    be appended to.
    :param object context: This parameter will take the current blender context by default,
    or can be passed an explicit context.
    """
    self.layout.menu(TOPBAR_MT_Utilities.bl_idname)


def add_pipeline_menu():
    """
    This function adds the Parent "Pipeline" menu item by appending the pipeline_menu()
    function to the top bar editor class definition.
    """
    if not hasattr(bpy.types, TOPBAR_MT_Pipeline.bl_idname):
        bpy.utils.register_class(TOPBAR_MT_Pipeline)
        bpy.types.TOPBAR_MT_editor_menus.append(pipeline_menu)

    try:
        bpy.types.TOPBAR_MT_Pipeline.remove(import_menu)
        bpy.types.TOPBAR_MT_Pipeline.remove(export_menu)
        bpy.types.TOPBAR_MT_Pipeline.remove(utilities_menu)


    finally:
        bpy.types.TOPBAR_MT_Pipeline.append(import_menu)
        bpy.types.TOPBAR_MT_Pipeline.append(export_menu)
        bpy.types.TOPBAR_MT_Pipeline.append(utilities_menu)


def remove_parent_menu():
    """
    This function removes the Parent "Pipeline" menu item by removing the pipeline_menu()
    function from the top bar editor class definition.
    """
    if hasattr(bpy.types, TOPBAR_MT_Pipeline.bl_idname):
        bpy.utils.unregister_class(TOPBAR_MT_Pipeline)
        bpy.types.TOPBAR_MT_editor_menus.remove(pipeline_menu)
