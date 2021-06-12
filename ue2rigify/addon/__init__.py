# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
import sys
import importlib
from . import properties, operators
from .settings import tool_tips, viewport_settings
from .functions import scene, nodes, templates, utilities
from .ui import view_3d, node_editor, addon_preferences, exporter


bl_info = {
    "name": "UE to Rigify",
    "author": "Epic Games Inc.",
    "description": "Allows you to convert a given rig and its animations to a Rigify rig.",
    "blender": (2, 83, 0),
    "version": (1, 5, 8),
    "location": "3D View > Tools > UE to Rigify",
    "wiki_url": "https://epicgames.github.io/BlenderTools/ue2rigify/quickstart.html",
    "warning": "",
    "category": "Pipeline"
}


modules = (
    scene,
    nodes,
    view_3d,
    exporter,
    tool_tips,
    utilities,
    templates,
    operators,
    properties,
    node_editor,
    addon_preferences,
    viewport_settings
)

classes = (
    operators.ConvertToRigifyRig,
    operators.RevertToSourceRig,
    operators.BakeActionsToSourceRig,
    operators.FreezeRig,
    operators.UnFreezeRig,
    operators.SaveMetarig,
    operators.SaveRigNodes,
    operators.SyncRigActions,
    operators.RemoveTemplateFolder,
    operators.ImportRigTemplate,
    operators.ExportRigTemplate,
    operators.CreateNodesFromSelectedBones,
    operators.CreateLinkFromSelectedBones,
    operators.CombineSelectedNodes,
    operators.AlignActiveNodeSockets,
    operators.ConstrainSourceToDeform,
    operators.RemoveConstraints,
    operators.SwitchModes,
    operators.NullOperator,
    addon_preferences.Ue2RigifyAddonPreferences,
    view_3d.UE_RIGIFY_PT_RigTemplatePanel
)


def register():
    """
    This function registers the addon classes when the addon is enabled.
    """
    # add an index in the system path that will be swapped during the tools use to load metarigs
    sys.path.insert(0, '')

    # reload submodules
    for module in modules:
        importlib.reload(module)

    properties.register()
    nodes.register()

    for cls in classes:
        bpy.utils.register_class(cls)

    # add an event handler that will save and load  preferences from the blend file
    bpy.app.handlers.load_pre.append(utilities.pre_file_load)
    bpy.app.handlers.load_post.append(utilities.load_properties)
    bpy.app.handlers.save_pre.append(utilities.save_properties)


def unregister():
    """
    This function unregisters the addon classes when the addon is disabled.
    """
    # set the tool mode back to source mode
    window_manager_properties = bpy.context.window_manager.ue2rigify
    window_manager_properties.selected_mode = window_manager_properties.source_mode

    # remove event handlers
    bpy.app.handlers.load_pre.remove(utilities.pre_file_load)
    bpy.app.handlers.load_post.remove(utilities.load_properties)
    bpy.app.handlers.save_pre.remove(utilities.save_properties)

    # remove the added system path
    sys.path.pop(0)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    utilities.remove_pie_menu_hot_keys()
    utilities.remove_picker_object()
    node_editor.unregister()
    nodes.unregister()
    properties.unregister()
