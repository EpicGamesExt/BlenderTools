# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
from .constants import ToolInfo, Modes
from .core import scene, templates, utilities
from .settings import tool_tips


class UE2RigifyProperties(bpy.types.PropertyGroup):
    """
    Defines a property group that lives in the scene.
    """
    # --------------------- read/write properties ------------------
    context = {}

    # template variables
    saved_metarig_data: bpy.props.StringProperty(default='')
    saved_links_data: bpy.props.StringProperty(default='')
    saved_node_data: bpy.props.StringProperty(default='')

    # mode variables
    previous_mode: bpy.props.StringProperty(default=Modes.SOURCE.name)

    # node variables
    categorized_nodes = {}
    check_node_tree_for_updates: bpy.props.BoolProperty(default=False)
    current_nodes_and_links: bpy.props.IntProperty(default=0, update=scene.update_rig_constraints)

    # utility variables
    previous_viewport_settings = {}

    # --------------------- user interface properties ------------------
    source_rig: bpy.props.PointerProperty(
        poll=utilities.armature_poll,
        type=bpy.types.Object,
        update=utilities.initialize_template_paths
    )

    # view 3d properties
    new_template_name: bpy.props.StringProperty(
        default='',
        maxlen=35,
        description=tool_tips.new_template_name
    )
    overwrite_control_animations: bpy.props.BoolProperty(
        default=False,
        description=tool_tips.overwrite_animation
    )

    bake_every_bone: bpy.props.BoolProperty(
        default=True,
        name="Bake every bone",
        description=tool_tips.bake_every_bone
    )

    selected_starter_metarig_template: bpy.props.EnumProperty(
        name="Metarig",
        description=tool_tips.starter_metarig_template_tool_tip,
        items=templates.safe_get_starter_metarig_templates,
        update=scene.set_meta_rig,
    )

    selected_rig_template: bpy.props.EnumProperty(
        name="Rig Template",
        description=tool_tips.rig_template_tool_tip,
        items=templates.safe_populate_templates_dropdown,
        options={'ANIMATABLE'},
        update=templates.set_template,
        default=None
    )

    selected_mode: bpy.props.EnumProperty(
        name="Modes",
        description=tool_tips.mode_tool_tip,
        items=templates.safe_get_modes,
        options={'ANIMATABLE'},
        update=scene.switch_modes
    )

    # exporter properties
    selected_export_template: bpy.props.EnumProperty(
        name="Export Rig Template",
        description=tool_tips.export_template_tool_tip,
        items=templates.safe_get_rig_templates,
        options={'ANIMATABLE'}
    )

    # node editor properties
    mirror_constraints: bpy.props.BoolProperty(
        default=True,
        description=tool_tips.mirror_constraints
    )

    left_x_mirror_token: bpy.props.StringProperty(
        default='_l',
        maxlen=35,
        description=tool_tips.left_x_mirror_token
    )
    right_x_mirror_token: bpy.props.StringProperty(
        default='_r',
        maxlen=35,
        description=tool_tips.right_x_mirror_token
    )


def register():
    """
    Registers the property group class and adds it to the window manager context when the
    addon is enabled.
    """
    properties = getattr(bpy.types.Scene, ToolInfo.NAME.value, None)
    if not properties:
        bpy.utils.register_class(UE2RigifyProperties)
        bpy.types.Scene.ue2rigify = bpy.props.PointerProperty(type=UE2RigifyProperties)


def unregister():
    """
    Unregisters the property group class and deletes it from the window manager context when the
    addon is disabled.
    """
    properties = getattr(bpy.types.Scene, ToolInfo.NAME.value, None)
    if properties:
        bpy.utils.unregister_class(UE2RigifyProperties)
        del bpy.types.Scene.ue2rigify
