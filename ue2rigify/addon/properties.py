# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
from .functions import scene
from .functions import templates
from .functions import utilities
from .settings import tool_tips


class UE2RigifyProperties(bpy.types.PropertyGroup):
    """
    This class defines a property group that can be accessed through the blender api.
    """

    # --------------------- read only properties ---------------------
    module_name = __package__

    # template constants
    rig_templates_path = templates.get_rig_templates_path()
    default_template = 'unreal_mannequin'

    # scene constants
    rig_collection_name = 'Rig'
    extras_collection_name = 'Extras'
    constraints_collection_name = 'Constraints'
    fk_to_source_mode = 'FK_TO_SOURCE'
    source_to_deform_mode = 'SOURCE_TO_DEFORM'
    metarig_mode = 'METARIG'
    source_mode = 'SOURCE'
    control_mode = 'CONTROL'

    # node constants
    bone_tree_name = 'Bone Remapping Nodes'
    node_socket_name = 'Bone Node Socket'
    source_rig_object_name = 'Source Rig Object'
    source_rig_category = 'Source Rig Bones'
    control_rig_fk_category = 'Control Rig FK Bones'
    control_rig_deform_category = 'Control Rig Deform Bones'

    # utility constants
    picker_name = 'picker'

    # rigify constants
    widgets_collection_name = 'WGTS_rig'
    meta_rig_name = 'metarig'
    control_rig_name = 'rig'
    rig_ui_file_name = 'rig_ui.py'

    context = {}

    # --------------------- read/write properties ---------------------

    # template variables
    saved_metarig_data: bpy.props.StringProperty(default='')
    saved_links_data: bpy.props.StringProperty(default='')
    saved_node_data: bpy.props.StringProperty(default='')

    # scene variables
    previous_mode: bpy.props.StringProperty(default=source_mode)
    source_rig_name: bpy.props.StringProperty(default='', update=utilities.source_rig_picker_update)

    # node variables
    categorized_nodes = {}
    check_node_tree_for_updates: bpy.props.BoolProperty(default=False)
    current_nodes_and_links: bpy.props.IntProperty(default=0, update=scene.update_rig_constraints)

    # utility variables
    previous_viewport_settings = {}

    # --------------------- user interface properties ------------------

    # view 3d properties
    freeze_rig: bpy.props.BoolProperty(default=False)
    new_template_name: bpy.props.StringProperty(
        default='',
        maxlen=35,
        description=tool_tips.new_template_name
    )
    overwrite_control_animations: bpy.props.BoolProperty(
        default=False,
        description=tool_tips.overwrite_animation
    )

    selected_starter_metarig_template: bpy.props.EnumProperty(
        name="Metarig",
        description=tool_tips.starter_metarig_template_tool_tip,
        items=templates.safe_get_starter_metarig_templates,
        update=scene.set_meta_rig
    )

    selected_rig_template: bpy.props.EnumProperty(
        name="Rig Template",
        description=tool_tips.rig_template_tool_tip,
        items=templates.safe_populate_templates_dropdown,
        options={'ANIMATABLE'},
        update=templates.set_template
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
        default=False,
        description=tool_tips.mirror_constraints
    )

    left_x_mirror_token: bpy.props.StringProperty(
        default='',
        maxlen=35,
        description=tool_tips.left_x_mirror_token
    )
    right_x_mirror_token: bpy.props.StringProperty(
        default='',
        maxlen=35,
        description=tool_tips.right_x_mirror_token
    )


class UE2RigifySavedProperties(bpy.types.PropertyGroup):
    """
    This class defines a property group that will be stored in the blender scene. This
    data will get serialized into the blend file when it is saved.
    """


def register():
    """
    This function registers the property group class and adds it to the window manager context when the
    addon is enabled.
    """
    bpy.utils.register_class(UE2RigifyProperties)
    bpy.utils.register_class(UE2RigifySavedProperties)

    bpy.types.WindowManager.ue2rigify = bpy.props.PointerProperty(type=UE2RigifyProperties)
    bpy.types.Scene.ue2rigify = bpy.props.PointerProperty(type=UE2RigifySavedProperties)


def unregister():
    """
    This function unregisters the property group class and deletes it from the window manager context when the
    addon is disabled.
    """
    bpy.utils.unregister_class(UE2RigifyProperties)

    del bpy.types.WindowManager.ue2rigify
    del bpy.types.Scene.ue2rigify
