# Copyright Epic Games, Inc. All Rights Reserved.
import bpy


class TOPBAR_MT_Export(bpy.types.Menu):
    """
    This defines a new class that will be the  menu, "Export".
    """
    bl_idname = "TOPBAR_MT_Export"
    bl_label = "Export"

    def draw(self, context):
        self.layout.operator('wm.send2ue')


class TOPBAR_MT_Pipeline(bpy.types.Menu):
    """
    This defines a new class that will be the top most parent menu, "Pipeline".
    All the other action menu items are children of this.
    """
    bl_idname = "TOPBAR_MT_Pipeline"
    bl_label = "Pipeline"

    def draw(self, context):
        self.layout.menu(TOPBAR_MT_Export.bl_idname)


def pipeline_menu(self, context):
    """
    This function creates the parent menu item. This will be referenced in other functions
    as a means of appending and removing it's contents from the top bar editor class
    definition.

    :param object self: This refers the the Menu class definition that this function will
    be appended to.
    :param object context: This parameter will take the current blender context by default,
    or can be passed an explicit context.
    """
    self.layout.menu(TOPBAR_MT_Pipeline.bl_idname)


def add_parent_menu():
    """
    This function adds the Parent "Pipeline" menu item by appending the create_parent_menu()
    function to the top bar editor class definition.
    """
    bpy.types.TOPBAR_MT_editor_menus.append(pipeline_menu)


def remove_parent_menu():
    """
    This function removes the Parent "Pipeline" menu item by removing the create_parent_menu()
    function from the top bar editor class definition.
    """
    bpy.types.TOPBAR_MT_editor_menus.remove(pipeline_menu)