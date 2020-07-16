# Copyright Epic Games, Inc. All Rights Reserved.
import os
import bpy
import importlib
from . import operators
from . import properties
from .ui import header_menu, addon_preferences
from .functions import export, unreal, validations, utilities
from .dependencies import remote_execution

bl_info = {
    "name": "Send to Unreal",
    "author": "Epic Games Inc.",
    "version": (1, 3, 4),
    "blender": (2, 83, 0),
    "location": "Header > Pipeline > Export > Send to Unreal",
    "description": "Sends an asset to the first open Unreal Editor instance on your machine.",
    "warning": "",
    "wiki_url": "https://github.com/EpicGames/BlenderTools/wiki/Send-to-Unreal-Home",
    "category": "Pipeline",
}


modules = [
    export,
    unreal,
    utilities,
    properties,
    validations,
    remote_execution,
    addon_preferences,
]

classes = [
    operators.Send2Ue,
    operators.SetupProject,
    operators.SetSceneScale,
    addon_preferences.SendToUnrealPreferences,
    header_menu.TOPBAR_MT_Pipeline,
    header_menu.TOPBAR_MT_Export,
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

    # add a event handler that will setup the scene as soon as the dependency graph updates
    bpy.app.handlers.depsgraph_update_post.append(utilities.check_for_armature_objects)

    # if a pipeline menu exists don't register the pipeline menu items
    if os.environ.get('PIPELINE_MENU'):
        classes.remove(header_menu.TOPBAR_MT_Pipeline)
        classes.remove(header_menu.TOPBAR_MT_Export)
    else:
        header_menu.add_parent_menu()

    # register the classes
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    """
    This function unregisters the addon classes when the addon is disabled.
    """
    # if need remove the pipeline menu
    if os.environ.get('PIPELINE_MENU'):
        del os.environ['PIPELINE_MENU']
    else:
        header_menu.remove_parent_menu()

    # unregister the classes
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # remove event handlers
    bpy.app.handlers.load_post.remove(utilities.setup_project)
    bpy.app.handlers.load_post.remove(utilities.load_properties)
    bpy.app.handlers.save_pre.remove(utilities.save_properties)
    bpy.app.handlers.depsgraph_update_post.remove(utilities.check_for_armature_objects)

    # unregister the properties
    properties.unregister()
