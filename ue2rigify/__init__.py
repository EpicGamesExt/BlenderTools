# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
import os
import importlib
from . import properties, operators, constants
from .settings import tool_tips, viewport_settings
from .core import scene, nodes, templates, utilities, validations
from .ui import view_3d, node_editor, addon_preferences, exporter


bl_info = {
    "name": "UE to Rigify",
    "author": "Epic Games Inc.",
    "description": "Allows you to drive a given rig and its animations with a Rigify rig.",
    "version": (1, 6, 2),
    "blender": (3, 3, 0),
    "location": "3D View > Tools > UE to Rigify",
    "wiki_url": "https://epicgames.github.io/BlenderTools/ue2rigify",
    "warning": "",
    "category": "Pipeline"
}


modules = [
    constants,
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
    viewport_settings,
    validations
]


def register():
    """
    Registers the addon classes when the addon is enabled.
    """
    # TODO remove this when new undo is stable
    bpy.context.preferences.experimental.use_undo_legacy = True

    templates.copy_default_templates()

    # reload the submodules
    if os.environ.get('UE2RIGIFY_DEV'):
        for module in modules:
            importlib.reload(module)

    properties.register()
    addon_preferences.register()
    view_3d.register()
    operators.register()
    nodes.register()


def unregister():
    """
    Unregisters the addon classes when the addon is disabled.
    """
    nodes.remove_pie_menu_hot_keys()
    node_editor.unregister()
    nodes.unregister()
    operators.unregister()
    view_3d.unregister()
    addon_preferences.unregister()
    properties.unregister()
