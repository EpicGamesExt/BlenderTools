# Copyright Epic Games, Inc. All Rights Reserved.

import time
from . import utilities
from ..dependencies import remote_execution

unreal_response = ''


def run_unreal_python_commands(remote_exec, commands, failed_connection_attempts=0):
    """
    This function finds the open unreal editor with remote connection enabled, and sends it python commands.

    :param object remote_exec: A RemoteExecution instance.
    :param str commands: A formatted string of python commands that will be run by the engine.
    :param int failed_connection_attempts: A counter that keeps track of how many times an editor connection attempt
    was made.
    """
    # wait a tenth of a second before attempting to connect
    time.sleep(0.1)
    try:
        # try to connect to an editor
        for node in remote_exec.remote_nodes:
            remote_exec.open_command_connection(node.get("node_id"))

        # if a connection is made
        if remote_exec.has_command_connection():
            # run the import commands and save the response in the global unreal_response variable
            global unreal_response
            unreal_response = remote_exec.run_command(commands, unattended=False)

        # otherwise make an other attempt to connect to the engine
        else:
            if failed_connection_attempts < 50:
                run_unreal_python_commands(remote_exec, commands, failed_connection_attempts + 1)
            else:
                remote_exec.stop()
                utilities.report_error("Could not find an open Unreal Editor instance!")

    # shutdown the connection
    finally:
        remote_exec.stop()


def import_asset(asset_data, properties):
    """
    This function imports an asset to unreal based on the asset data in the provided dictionary.

    :param dict asset_data: A dictionary of import parameters.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    # start a connection to the engine that lets you send python strings
    remote_exec = remote_execution.RemoteExecution()
    remote_exec.start()

    # send over the python code as a string
    run_unreal_python_commands(
        remote_exec,
        '\n'.join([
            f'import_task = unreal.AssetImportTask()',
            f'import_task.filename = r"{asset_data.get("fbx_file_path")}"',
            f'import_task.destination_path = r"{asset_data.get("game_path")}"',
            f'import_task.automated = {not properties.advanced_ui_import}',
            f'import_task.replace_existing = True',
            f'options = unreal.FbxImportUI()',
            f'options.auto_compute_lod_distances = False',
            f'options.lod_number = 0',
            f'options.import_as_skeletal = {bool(asset_data.get("skeletal_mesh"))}',
            f'options.import_animations = {bool(asset_data.get("animation"))}',
            f'options.import_materials = {properties.import_materials}',
            f'options.import_textures = {properties.import_textures}',
            f'options.import_mesh = {bool(asset_data.get("import_mesh"))}',
            f'options.static_mesh_import_data.generate_lightmap_u_vs = False',
            f'options.lod_distance0 = 1.0',

            # if this is a skeletal mesh import
            f'if {bool(asset_data.get("skeletal_mesh"))}:',
            f'\toptions.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH',
            f'\toptions.skeletal_mesh_import_data.import_mesh_lo_ds = {bool(asset_data.get("lods"))}',
            f'\toptions.skeletal_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS',

            # if this is an static mesh import
            f'if {not bool(asset_data.get("skeletal_mesh"))}:',
            f'\toptions.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH',
            f'\toptions.static_mesh_import_data.import_mesh_lo_ds = {bool(asset_data.get("lods"))}',
            f'\toptions.static_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS',

            # try to load the provided skeleton
            f'skeleton_asset = unreal.load_asset(r"{asset_data.get("skeleton_game_path")}")',
            f'if skeleton_asset:',
            f'\toptions.set_editor_property("skeleton", skeleton_asset)',

            # if this is an animation import
            f'if {bool(asset_data.get("animation"))}:',
            f'\toptions.set_editor_property("original_import_type", unreal.FBXImportType.FBXIT_ANIMATION)',
            f'\toptions.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)',
            f'\toptions.anim_sequence_import_data.set_editor_property("preserve_local_transform", True)',

            # assign the options object to the import task and import the asset
            f'import_task.options = options',
            f'unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([import_task])',

            # check for a that the game asset imported correctly if the import object name as is False
            f'if {not properties.import_object_name_as_root}:',
            f'\tgame_asset = unreal.load_asset(r"{asset_data.get("game_path")}")',
            f'\tif not game_asset:',
            f'\t\traise RuntimeError("Multiple roots are found in the bone hierarchy. Unreal will only support a single root bone.")',
        ]))

    # if there is an error report it
    if unreal_response:
        if unreal_response['result'] != 'None':
            utilities.report_error(unreal_response['result'])
            return False
    return True


def asset_exists(game_path):
    """
    This function checks to see if an asset exist in unreal.

    :param str game_path: The game path to the unreal asset.
    :return bool: Whether or not the asset exists.
    """
    # start a connection to the engine that lets you send python strings
    remote_exec = remote_execution.RemoteExecution()
    remote_exec.start()

    # send over the python code as a string
    run_unreal_python_commands(
        remote_exec,
        '\n'.join([
            f'game_asset = unreal.load_asset(r"{game_path}")',
            f'if game_asset:',
            f'\tpass',
            f'else:',
            f'\traise RuntimeError("Asset not found")',
        ]))

    return bool(unreal_response['success'])


def delete_asset(game_path):
    """
    This function deletes an asset in unreal.

    :param str game_path: The game path to the unreal asset.
    """
    # start a connection to the engine that lets you send python strings
    remote_exec = remote_execution.RemoteExecution()
    remote_exec.start()

    # send over the python code as a string
    run_unreal_python_commands(
        remote_exec,
        '\n'.join([
            f'unreal.EditorAssetLibrary.delete_asset(r"{game_path}")',
        ]))
