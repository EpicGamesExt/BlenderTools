# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
from ..constants import Template, Modes


class UE_RIGIFY_PT_RigTemplatePanel(bpy.types.Panel):
    """
    This class defines the user interface for the panel in the tab in the 3d view
    """
    bl_label = 'UE to Rigify Toolkit'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'UE to Rigify'

    def draw(self, context):
        """
        This function overrides the draw method in the Panel class. The draw method is the function that
        defines the user interface layout and gets updated routinely.

        :param object context: The 3d view context.
        """
        properties = bpy.context.scene.ue2rigify
        layout = self.layout

        # source rig selector
        box = layout.box()
        row = box.row()
        row = row.split(factor=0.90, align=True)
        row.prop(properties, 'source_rig', text='Source')

        # display an error message if rigify is not active
        rigify_enabled = bpy.context.preferences.addons.get('rigify')
        if not rigify_enabled:
            row = layout.row()
            row.alert = True
            row.label(text='Activate the Rigify addon!')

        # enable the layout if an armature is selected
        layout = layout.column()
        layout.enabled = bool(properties.source_rig)

        # template dropdown
        row = layout.row()
        row.label(text='Template:')
        if properties.selected_rig_template in [
            Template.DEFAULT_MALE_TEMPLATE,
            Template.DEFAULT_FEMALE_TEMPLATE,
            'create_new'
        ]:
            row = layout.row()
            row.prop(properties, 'selected_rig_template', text='')
        else:
            row = layout.split(factor=0.90, align=True)
            row.prop(properties, 'selected_rig_template', text='')
            row.operator('ue2rigify.remove_rig_template', icon='PANEL_CLOSE')

        # mode dropdown
        if properties.selected_rig_template != 'create_new':
            row = layout.row()
            row.label(text='Mode:')
            row = layout.row()
            row.prop(properties, 'selected_mode', text='')

        box = layout.box()
        row = box.row()
        row.label(text='Rig Template Editor', icon='TOOL_SETTINGS')

        # edit the metarig
        if properties.selected_mode == Modes.METARIG.name:

            row = box.row()

            # creating a new metarig
            if properties.selected_rig_template == 'create_new':
                row = box.row()
                row.prop(properties, 'selected_starter_metarig_template', text='Metarig')
                row = box.row()
                row.prop(properties, 'new_template_name', text='Name')
                row = box.row()
                row.enabled = properties.new_template_name != ''

            row.operator('ue2rigify.save_metarig')

        # edit nodes mode
        if properties.selected_mode in [Modes.FK_TO_SOURCE.name, Modes.SOURCE_TO_DEFORM.name]:
            row = box.row()
            row.operator('ue2rigify.save_rig_nodes')

        # control mode
        if properties.selected_mode == Modes.CONTROL.name:
            row = box.row()
            row.prop(properties, 'bake_every_bone')
            row = box.row()
            row.scale_y = 2.0
            row.operator('ue2rigify.revert_to_source_rig')
            row.operator('ue2rigify.bake_from_rig_to_rig', text='Bake')

        # source mode
        if properties.selected_mode == Modes.SOURCE.name:
            row = box.row()
            row.prop(properties, 'overwrite_control_animations', text='Overwrite Animation')
            row = box.row()
            row.scale_y = 2.0
            row.operator('ue2rigify.convert_to_control_rig', text='Convert')


class VIEW3D_PIE_MT_CreateNodes(bpy.types.Menu):
    bl_label = 'Create Nodes'
    bl_idname = 'VIEW3D_PIE_MT_CreateNodes'

    def draw(self, context):
        """
        This function overrides the draw method in the Menu class. The draw method is the function that
        defines the user interface layout and gets updated routinely.

        :param object context: The 3d view context.
        """
        layout = self.layout
        pie = layout.menu_pie()

        # pie menu operators
        pie.operator('ue2rigify.create_nodes_from_selected_bones')
        pie.operator('ue2rigify.create_link_from_selected_bones')


def register():
    """
    Registers the view 3d panel when the addon is enabled.
    """
    if not hasattr(bpy.types, UE_RIGIFY_PT_RigTemplatePanel.__name__):
        bpy.utils.register_class(UE_RIGIFY_PT_RigTemplatePanel)


def unregister():
    """
    Unregisters the view 3d panel when the addon is disabled.
    """
    if hasattr(bpy.types, UE_RIGIFY_PT_RigTemplatePanel.__name__):
        bpy.utils.unregister_class(UE_RIGIFY_PT_RigTemplatePanel)

