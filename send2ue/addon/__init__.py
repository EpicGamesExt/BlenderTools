# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
import importlib
from . import operators
from . import properties
from .dependencies import remote_execution
from .ui import header_menu, addon_preferences, importer
from .functions import export, unreal, validations, utilities

# NOTE: The blender version in the `bl_info` dictionary is for the minimum
#  blender version support and should only be changed when there's new
#  functionality that will break the addon

bl_info = {
    "name": "Send to Unreal",
    "author": "Epic Games Inc.",
    "version": (1, 6, 1),   # addon plugin version
    "blender": (2, 83, 0),  # minimum blender version
    "location": "Header > Pipeline > Export > Send to Unreal",
    "description": "Sends an asset to the first open Unreal Editor instance on your machine.",
    "warning": "",
    "wiki_url": "https://epicgames.github.io/BlenderTools/send2ue/quickstart.html",
    "category": "Pipeline",
}


modules = [
    export,
    unreal,
    importer,
    utilities,
    operators,
    properties,
    validations,
    remote_execution,
    addon_preferences,
]

classes = [
    operators.Send2Ue,
    operators.AdvancedSend2Ue,
    operators.ImportAsset,
    operators.NullOperator,
    addon_preferences.SendToUnrealPreferences,
    header_menu.TOPBAR_MT_Export,
    header_menu.TOPBAR_MT_Import
]


def register():
    """
    This function registers the addon classes when the addon is enabled.
    """
    # reload the submodules
    for module in modules:
        importlib.reload(module)

    # register the properties
    properties.register()

    # add a function to the event timer that will fire after the addon is enabled
    bpy.app.timers.register(utilities.addon_enabled)

    # add an event handler that will save and load  preferences from the blend file
    bpy.app.handlers.load_post.append(utilities.setup_project)
    bpy.app.handlers.load_post.append(utilities.load_properties)
    bpy.app.handlers.save_pre.append(utilities.save_properties)

    # register the classes
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """
    This function unregisters the addon classes when the addon is disabled.
    """
    # remove the pipeline menu
    header_menu.remove_parent_menu()

    # unregister the classes
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # remove event handlers
    bpy.app.handlers.load_post.remove(utilities.setup_project)
    bpy.app.handlers.load_post.remove(utilities.load_properties)
    bpy.app.handlers.save_pre.remove(utilities.save_properties)

    # unregister the properties
    properties.unregister()
