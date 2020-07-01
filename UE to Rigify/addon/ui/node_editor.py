# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
import nodeitems_utils


class UE_RIGIFY_PT_NodeToolsPanel(bpy.types.Panel):
    """
    This class defines the user interface for the panel in the tool tab in the node editor
    """
    bl_label = "Node Tools"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Tool"

    def draw(self, context):
        """
        This function overrides the draw method in the Panel class. The draw method is the function that
        defines the user interface layout and gets updated routinely.

        :param object context: The node editor context.
        """
        properties = bpy.context.window_manager.ue2rigify

        layout = self.layout

        row = layout.row()
        row.prop(properties, 'mirror_constraints', text='X-axis Mirror')

        row = layout.row()
        if not properties.mirror_constraints:
            row.enabled = False
        row.label(text="Right:")
        row.label(text="Left:")

        row = layout.row()
        if not properties.mirror_constraints:
            row.enabled = False
        row.prop(properties, 'right_x_mirror_token', text='')
        row.prop(properties, 'left_x_mirror_token', text='')

        row = layout.row()
        row.scale_y = 2.0
        row.operator('wm.align_active_node_sockets')

        row = layout.row()
        row.scale_y = 2.0
        row.operator('wm.combine_selected_nodes')


class BoneRemappingTreeNode:
    """
    This class defines the node tree
    """
    @classmethod
    def poll(cls, node_tree):
        """
        This method checks to see if the node tree has the correct bl_idname.

        :param object node_tree: A given node tree object
        :return bool: True or false depending on whether the bl_idname of the provided node tree matches the
        bl_idname in the properties.
        """
        properties = bpy.context.window_manager.ue2rigify
        return node_tree.bl_idname == properties.bone_tree_name.replace(' ', '')


class BoneRemappingTreeCategory(nodeitems_utils.NodeCategory):
    @classmethod
    def poll(cls, context):
        """
        This method checks to see if the node tree category is the correct type.

        :param object context: A given node tree category
        :return bool: True or false depending on whether the type of the node tree in the context matches the
        type in the properties.
        """
        properties = bpy.context.window_manager.ue2rigify
        return context.space_data.tree_type == properties.bone_tree_name.replace(' ', '')


class BaseRigBonesNode(bpy.types.Node, BoneRemappingTreeNode):
    """
    This class defines the base node class the will be subclassed.
    """
    def draw_label(self):
        """
        This function overrides the draw_label method in the Node class. The draw method is the function that
        defines the label of the node in the user interface.

        :return str: The name of the label.
        """
        return self.bl_label


def register():
    """
    When called, this function registers the node panel class.
    """
    try:
        bpy.utils.register_class(UE_RIGIFY_PT_NodeToolsPanel)
    except ValueError:
        pass


def unregister():
    """
    When called, the function unregisters the node panel class.
    """
    try:
        bpy.utils.unregister_class(UE_RIGIFY_PT_NodeToolsPanel)
    except RuntimeError:
        pass
