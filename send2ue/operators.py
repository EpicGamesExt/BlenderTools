# Copyright Epic Games, Inc. All Rights Reserved.

import os
import bpy
import queue
import threading
from .constants import ToolInfo, ExtensionTasks
from .core import export, utilities, settings, validations, extension
from .ui import file_browser, dialog
from .dependencies import unreal
from .dependencies.rpc import blender_server
from .properties import register_scene_properties, unregister_scene_properties


class Send2Ue(bpy.types.Operator):
    """Push your assets to disk and/or an open unreal editor instance"""
    bl_idname = "wm.send2ue"
    bl_label = "Push Assets"

    def __init__(self):
        self.timer = None
        self.escape = False
        self.done = False
        self.max_step = 0
        self.state = {}

        # add execution queue
        execution_queue = bpy.app.driver_namespace.get(ToolInfo.EXECUTION_QUEUE.value)
        if not execution_queue:
            bpy.app.driver_namespace[ToolInfo.EXECUTION_QUEUE.value] = queue.Queue()
        self.execution_queue = bpy.app.driver_namespace[ToolInfo.EXECUTION_QUEUE.value]

    @staticmethod
    def draw_progress(self, context):
        self.layout.prop(context.window_manager.send2ue, 'progress')

    def modal(self, context, event):
        if not self.done:
            context.area.tag_redraw()

        if self.execution_queue.empty():
            self.done = True

        if event.type == 'ESC':
            self.escape = True
            # clears the queue in a thread safe manner
            with self.execution_queue.mutex:
                self.execution_queue.queue.clear()

        if event.type == 'TIMER':
            if not self.execution_queue.empty():
                try:
                    function, args, kwargs, message, asset_id, attribute = self.execution_queue.get()
                    step = self.max_step - self.execution_queue.qsize()
                    context.window_manager.send2ue.progress = abs(((step / self.max_step) * 100) - 1)
                    utilities.refresh_all_areas()

                    # set the current asset id
                    context.window_manager.send2ue.asset_id = asset_id
                    # run the function
                    function(*args, **kwargs)

                    # get the description
                    file_name = context.window_manager.send2ue.asset_data[asset_id].get(attribute)
                    description = message.format(
                        attribute=utilities.get_asset_name_from_file_name(file_name)
                    )
                    bpy.context.workspace.status_text_set_internal(description)
                except Exception as error:
                    self.escape_operation(context)
                    raise error

            if self.escape:
                bpy.types.STATUSBAR_HT_header.remove(self.draw_progress)
                context.window_manager.event_timer_remove(self.timer)
                bpy.context.workspace.status_text_set_internal(None)
                self.post_operation()
                return {'FINISHED'}

            if self.done:
                context.window_manager.send2ue.progress = 100
                bpy.context.workspace.status_text_set_internal('Finished!')
                bpy.context.window_manager.progress_end()
                self.escape = True
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if utilities.is_unreal_connected():
            properties = bpy.context.scene.send2ue
            self.pre_operation()

            # initialize the progress bar
            self.execution_queue.queue.clear()
            context.window_manager.send2ue.progress = 0
            bpy.context.workspace.status_text_set_internal('Validating...')

            # run the full send to unreal operation which queues all the jobs
            try:
                export.send2ue(properties)
            # if validations fail
            except Exception as error:
                self.escape_operation(context)
                # if in dev mode raise the error instead of reporting it
                if os.environ.get('SEND2UE_DEV'):
                    raise error

                self.report({'ERROR'}, str(error))
                return {'FINISHED'}

            self.max_step = self.execution_queue.qsize()

            # start a timer in the operators modal that processes the queued jobs
            context.window_manager.modal_handler_add(self)
            self.timer = context.window_manager.event_timer_add(0.01, window=context.window)
            bpy.types.STATUSBAR_HT_header.prepend(self.draw_progress)

            return {'RUNNING_MODAL'}
        else:
            return {'FINISHED'}

    def execute(self, context):
        if utilities.is_unreal_connected():
            properties = bpy.context.scene.send2ue
            self.pre_operation()

            self.execution_queue.queue.clear()
            export.send2ue(properties)

            # process the queued functions
            while not self.execution_queue.empty():
                function, args, kwargs, message, asset_id, attribute = self.execution_queue.get()
                # set the current asset id
                context.window_manager.send2ue.asset_id = asset_id
                # run the function
                function(*args, **kwargs)

            self.post_operation()
        return {'FINISHED'}

    def escape_operation(self, context):
        if self.timer:
            bpy.types.STATUSBAR_HT_header.remove(self.draw_progress)
            context.window_manager.event_timer_remove(self.timer)
        bpy.context.workspace.status_text_set_internal(None)
        self.post_operation()
        return {'FINISHED'}

    def pre_operation(self):
        # get the current state of the scene and its objects
        self.state['context'] = utilities.get_current_context()

        # unpack the textures for export if needed
        self.state['unpacked_files'] = utilities.unpack_textures()

        # sets the current frame to 0
        bpy.context.scene.frame_current = 0

        # run the pre export extensions
        extension.run_extension_tasks(ExtensionTasks.PRE_OPERATION.value)

    def post_operation(self):
        # run the post export extensions
        extension.run_extension_tasks(ExtensionTasks.POST_OPERATION.value)

        # repack the unpacked files
        utilities.remove_unpacked_files(self.state.get('unpacked_files', {}))

        # restore the previous state of the scene and its objects
        utilities.set_context(self.state.get('context', {}))


class SettingsDialog(bpy.types.Operator, dialog.Send2UnrealDialog):
    """Open the settings dialog to modify the tool properties"""
    bl_idname = "wm.settings_dialog"
    bl_label = "Settings Dialog"

    def execute(self, context):
        properties = bpy.context.scene.send2ue
        export.send2ue(properties)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self, width=600)


class ImportAsset(bpy.types.Operator, file_browser.ImportAsset):
    """Import a file that came from unreal"""
    bl_idname = "wm.import_asset"
    bl_label = "Import Asset"
    filename_ext = ".fbx"

    def execute(self, context):
        properties = bpy.context.scene.send2ue
        validation_manager = validations.ValidationManager(properties)
        validation_manager.validate_scene_scale()
        utilities.import_asset(self.filepath, bpy.context.window_manager.send2ue)
        return {'FINISHED'}


class CreatePredefinedCollections(bpy.types.Operator):
    """Creates the pre-defined collection 'Export' that is needed to collect asset data."""
    bl_idname = "send2ue.create_predefined_collections"
    bl_label = "Create Pre-defined Collections"

    def execute(self, context):
        utilities.create_collections()
        return {'FINISHED'}


class SaveTemplate(bpy.types.Operator, file_browser.ExportTemplate):
    """Saves the current state of the properties to the specified template file"""
    bl_idname = 'send2ue.save_template'
    bl_label = 'Save Template'
    filename_ext = '.json'

    def execute(self, context):
        settings.save_template(self.filepath)
        return {'FINISHED'}


class LoadTemplate(bpy.types.Operator, file_browser.ImportTemplate):
    """Loads the specified template file into the template folder location"""
    bl_idname = 'send2ue.load_template'
    bl_label = 'Load Template'
    filename_ext = '.json'

    def execute(self, context):
        settings.load_template(self.filepath)
        return {'FINISHED'}


class RemoveTemplate(bpy.types.Operator):
    """Remove the selected settings template"""
    bl_idname = "send2ue.remove_template"
    bl_label = "Delete this template?"

    def execute(self, context):
        properties = bpy.context.scene.send2ue
        settings.remove_template(properties)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_confirm(self, event)


class ReloadExtensions(bpy.types.Operator):
    """Reload the extensions files"""
    bl_idname = "send2ue.reload_extensions"
    bl_label = "Reload Extensions"

    def execute(self, context):
        addon = bpy.context.preferences.addons.get(ToolInfo.NAME.value)
        if addon:
            extensions_repo_path = addon.preferences.extensions_repo_path
            if extensions_repo_path:
                if not os.path.exists(extensions_repo_path) or not os.path.isdir(
                    extensions_repo_path
                ):
                    self.report(f'"{extensions_repo_path}" is not a folder path on disk.')
                    return {'FINISHED'}

        extension_factory = extension.ExtensionFactory()

        # remove the extension operators
        extension_factory.remove_utility_operators()

        # remove the properties
        unregister_scene_properties()

        # re-create the utility operators
        extension_factory.create_utility_operators()

        # re-create the properties again
        register_scene_properties()

        return {'FINISHED'}


class StartRPCServers(bpy.types.Operator):
    """Bootstraps unreal and blender with rpc server threads, so that they are ready for remote calls."""
    bl_idname = 'send2ue.start_rpc_servers'
    bl_label = 'Start RPC Servers'

    def execute(self, context):
        # ensure the open unreal editor is bootstrapped with the rpc server
        utilities.is_unreal_connected()

        # start the blender rpc server if its not already running
        if 'BlenderRPCServer' not in [thread.name for thread in threading.enumerate()]:
            rpc_server = blender_server.RPCServer()
            rpc_server.start(threaded=True)

        return {'FINISHED'}


class NullOperator(bpy.types.Operator):
    """This is an operator that changes nothing, but it used to clear the undo stack"""
    bl_idname = 'send2ue.null_operator'
    bl_label = 'Null Operator'

    def execute(self, context):
        return {'FINISHED'}


operator_classes = [
    Send2Ue,
    SettingsDialog,
    ImportAsset,
    CreatePredefinedCollections,
    RemoveTemplate,
    SaveTemplate,
    LoadTemplate,
    ReloadExtensions,
    StartRPCServers,
    NullOperator,
]


def register():
    """
    Registers the operators.
    """
    for operator_class in operator_classes:
        if not utilities.get_operator_class_by_bl_idname(operator_class.bl_idname):
            bpy.utils.register_class(operator_class)

    # register the extension utility operators
    extension_factory = extension.ExtensionFactory()
    extension_factory.create_utility_operators()


def unregister():
    """
    Unregisters the operators.
    """
    # remove the extension operators
    extension_factory = extension.ExtensionFactory()
    extension_factory.remove_utility_operators()

    # unregister the classes
    for operator_class in operator_classes:
        if utilities.get_operator_class_by_bl_idname(operator_class.bl_idname):
            bpy.utils.unregister_class(operator_class)

