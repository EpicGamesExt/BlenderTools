# Copyright Epic Games, Inc. All Rights Reserved.

import os
import bpy
from ..dependencies.unreal import UnrealRemoteCalls, is_connected


def set_property_error_message(property_name, error_message):
    """
    Set an error message on the given property.

    :param str property_name: The name of the property.
    :param str error_message: The error message.
    """
    bpy.context.window_manager.send2ue.property_errors[f'{property_name}_error_message'] = error_message


def resolve_path(path):
    """
    Checks if a given path is relative and returns the full
    path else returns the original path

    :param str path: The input path
    :return str: The expanded path
    """
    # Check for a relative path input. Relative paths are represented
    # by '//' eg. '//another/path/relative/to/blend_file'
    if path.startswith('//') or path.startswith('./'):
        # Build an absolute path resolving the relative path from the blend file
        path = os.path.join(
            os.path.dirname(bpy.data.filepath),
            path.replace("//", "./")
        )
    return os.path.normpath(os.path.abspath(path))


def format_asset_path(game_reference):
    """
    Removes the extra characters if a game reference is pasted in.

    :param str game_reference: The game reference copied to the clipboard from the unreal asset.
    :return str: The formatted game folder path.
    """
    if game_reference[-1] == "'":
        return game_reference.split("'")[-2].split(".")[0]

    if not game_reference.startswith('/'):
        game_reference = f'/{game_reference}'

    return game_reference


def format_folder_path(game_reference):
    """
    Removes the asset name if a game reference is pasted in.

    :param str game_reference: The game reference copied to the clipboard from the unreal asset.
    :return str: The formatted game folder path.
    """
    folder_path = game_reference.replace('\\', '/').replace(r'\\', '/').replace('//', '/')

    if folder_path:
        if folder_path[-1] == "'":
            asset_name = format_asset_path(folder_path).split('/')[-1]
            folder_path = format_asset_path(folder_path).replace(asset_name, '')

        if not folder_path.endswith('/'):
            folder_path = f'{folder_path}/'

    return folder_path


def auto_format_unreal_folder_path(name, properties):
    """
    Formats a unreal folder path.

    :param str name: The name of the changed property.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    error_message = None
    # don't run the validations if path validation is false
    if not bpy.context.window_manager.send2ue.path_validation:
        return

    # clear the error message value
    set_property_error_message(name, '')

    value = getattr(properties, name)
    formatted_value = format_folder_path(value)
    if value:
        if value != formatted_value:
            setattr(properties, name, formatted_value)

            # Ensure unreal editor is open
            if not is_connected():
                error_message = f'No Unreal Editor connection. Folder path "{formatted_value}" can not be validated.'
                set_property_error_message(
                    name,
                    error_message
                )
                return error_message

    # Make sure the mesh path to unreal is correct as the engine will hard crash if passed an incorrect path
    if not formatted_value:
        error_message = 'Please specify a folder in your unreal project where your asset will be imported.'
        set_property_error_message(
            name,
            error_message
        )
    elif not len(formatted_value.split('/')) >= 2:
        error_message = 'Please specify at least a root folder location.'
        set_property_error_message(
            name,
            error_message
        )
    elif not error_message and not UnrealRemoteCalls.directory_exists('/'.join(formatted_value.split('/')[:2])):
        root_folder = '/'.join(formatted_value.split('/')[:2])
        error_message = f'The root folder "{root_folder}" does not exist in your unreal project.'
        set_property_error_message(
            name,
            error_message
        )
    return error_message


def auto_format_disk_folder_path(name, properties):
    """
    Formats a disk folder path.

    :param str name: The name of the changed property.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    error_message = ''
    set_property_error_message(name, error_message)
    # don't run the validations if path validation is false
    if not bpy.context.window_manager.send2ue.path_validation:
        return

    value = getattr(properties, name)
    formatted_value = value.replace('"', '').replace("'", '')
    if value != formatted_value:
        setattr(properties, name, formatted_value)

        if bpy.data.filepath and formatted_value.startswith(('//', './', '.\\')):
            formatted_value = resolve_path(formatted_value)

        elif formatted_value.startswith(('//', './', '.\\')):
            error_message = 'Relative paths can only be used if this file is saved.'

        # check that the folder exists
        if os.path.exists(formatted_value):
            # test the folder permissions
            if not os.access(formatted_value, os.W_OK):
                error_message = f'The permissions of "{formatted_value}" will not allow files to write to it.'
        else:
            error_message = f'"{formatted_value}" does not exist on disk.'

        set_property_error_message(
            name,
            error_message
        )

    return error_message


def auto_format_unreal_asset_path(name, properties):
    """
    Formats a unreal asset path.

    :param str name: The name of the changed property.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    error_message = None
    # don't run the validations if path validation is false
    if not bpy.context.window_manager.send2ue.path_validation:
        return

    # clear the error message value
    set_property_error_message(name, '')

    value = getattr(properties, name)
    if value:
        formatted_value = format_asset_path(value)
        if value != formatted_value:
            setattr(properties, name, formatted_value)

        # Ensure unreal editor is open
        if not is_connected():
            error_message = (
                f'No Unreal Editor connection. Asset path "{formatted_value}" can not be validated.'
            )
            set_property_error_message(
                name,
                error_message
            )
            return error_message

        if not error_message and not UnrealRemoteCalls.asset_exists(formatted_value):
            error_message = f'Asset "{formatted_value}" does not exist in unreal.'
            set_property_error_message(
                name,
                error_message
            )
    return error_message


def update_unreal_mesh_folder_path(self, context):
    """
    Called every time the unreal mesh folder path is updated.

    :param object self: This is a reference to the property data object.
    :param object context: The context when the property was called.
    """
    auto_format_unreal_folder_path('unreal_mesh_folder_path', self)


def update_unreal_animation_folder_path(self, context):
    """
    Called every time the unreal animation folder path is updated.

    :param object self: This is a reference to the property data object.
    :param object context: The context when the property was called.
    """
    auto_format_unreal_folder_path('unreal_animation_folder_path', self)


def update_unreal_groom_folder_path(self, context):
    """
    Called every time the unreal groom folder path is updated.

    :param object self: This is a reference to the property data object.
    :param object context: The context when the property was called.
    """
    auto_format_unreal_folder_path('unreal_groom_folder_path', self)


def update_unreal_skeleton_asset_path(self, context):
    """
    Called every time the unreal skeleton asset path is updated.

    :param object self: This is a reference to the property data object.
    :param object context: The context when the property was called.
    """
    name = 'unreal_skeleton_asset_path'
    error_message = auto_format_unreal_asset_path(name, self)
    value = getattr(self, name)
    if value and not error_message:
        asset_type = UnrealRemoteCalls.get_asset_type(value)
        if asset_type != 'Skeleton':
            error_message = f'This is a {asset_type} asset. This must be a Skeleton asset.'
            set_property_error_message(
                name,
                error_message
            )


def update_unreal_physics_asset_path(self, context):
    """
    Called every time the unreal physics asset path is updated.

    :param object self: This is a reference to the property data object.
    :param object context: The context when the property was called.
    """
    auto_format_unreal_asset_path('unreal_physics_asset_path', self)


def update_unreal_skeletal_mesh_lod_settings_path(self, context):
    """
    Called every time the unreal skeletal mesh lod settings asset path is updated.

    :param object self: This is a reference to the property data object.
    :param object context: The context when the property was called.
    """
    auto_format_unreal_asset_path('unreal_skeletal_mesh_lod_settings_path', self)


def update_disk_mesh_folder_path(self, context):
    """
    Called every time the disk mesh folder path is updated.

    :param object self: This is a reference to the property data object.
    :param object context: The context when the property was called.
    """
    auto_format_disk_folder_path('disk_mesh_folder_path', self)


def update_disk_animation_folder_path(self, context):
    """
    Called every time the disk animation folder path is updated.

    :param object self: This is a reference to the property data object.
    :param object context: The context when the property was called.
    """
    auto_format_disk_folder_path('disk_animation_folder_path', self)

def update_disk_groom_folder_path(self, context):
    """
    Called every time the disk groom folder path is updated.

    :param object self: This is a reference to the property data object.
    :param object context: The context when the property was called.
    """
    auto_format_disk_folder_path('disk_groom_folder_path', self)
