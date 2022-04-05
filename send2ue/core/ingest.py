# Copyright Epic Games, Inc. All Rights Reserved.

from . import settings, extension
from ..constants import PathModes, ExtensionOperators
from ..dependencies.unreal import UnrealRemoteCalls
from .utilities import track_progress, get_asset_id


@track_progress(message='Importing asset "{attribute}"...', attribute='file_path')
def import_asset(asset_id, properties, property_data):
    """
    Imports an asset to unreal based on the asset data in the provided dictionary.

    :param str asset_id: The unique id of the asset.
    :param PropertyData properties: A property data instance that contains all property values of the tool.
    :param dict property_data: A dictionary representation of the properties.
    """
    # set the current asset id
    properties.asset_id = asset_id

    # run the pre import extensions
    extension.run_operators(ExtensionOperators.PRE_IMPORT.value)

    # get the asset data
    asset_data = properties.asset_data[properties.asset_id]

    # import the asset
    UnrealRemoteCalls.import_asset(asset_data.get('file_path'), asset_data, property_data)

    # import fcurves
    if asset_data.get('fcurve_file_path'):
        import_animation_fcurves(asset_id, properties)

    # run the post import extensions
    extension.run_operators(ExtensionOperators.POST_IMPORT.value)


@track_progress(message='Importing fcurves on "{attribute}"...', attribute='asset_path')
def import_animation_fcurves(asset_id, properties):
    """
    Imports fcurves from a file onto an animation sequence.

    :param str asset_id: The unique id of the asset.
    :param PropertyData properties: A property data instance that contains all property values of the tool.
    """
    asset_data = properties.asset_data[asset_id]
    UnrealRemoteCalls.import_animation_fcurves(
        asset_data.get('asset_path'),
        asset_data.get('fcurve_file_path')
    )


@track_progress(message='Creating static mesh sockets for "{attribute}"...', attribute='asset_path')
def create_static_mesh_sockets(asset_id, properties):
    """
    Creates sockets on a static mesh.

    :param str asset_id: The unique id of the asset.
    :param PropertyData properties: A property data instance that contains all property values of the tool.
    """
    asset_data = properties.asset_data[asset_id]
    UnrealRemoteCalls.set_static_mesh_sockets(
        asset_data.get('asset_path'),
        asset_data
    )


@track_progress(message='Resetting lods for "{attribute}"...', attribute='asset_path')
def reset_lods(asset_id, properties, property_data):
    """
    Removes all lods on the given mesh.

    :param str asset_id: The unique id of the asset.
    :param PropertyData properties: A property data instance that contains all property values of the tool.
    :param dict property_data: A dictionary representation of the properties.
    """
    asset_data = properties.asset_data[asset_id]
    asset_path = asset_data.get('asset_path')

    if asset_data.get('skeletal_mesh'):
        UnrealRemoteCalls.reset_skeletal_mesh_lods(asset_path, property_data)
    else:
        UnrealRemoteCalls.reset_static_mesh_lods(asset_path)


@track_progress(message='Importing lods for "{attribute}"...', attribute='asset_path')
def import_lod_files(asset_id, properties):
    """
    Imports lods onto a mesh.

    :param str asset_id: The unique id of the asset.
    :param PropertyData properties: A property data instance that contains all property values of the tool.
    """
    asset_data = properties.asset_data[asset_id]
    lods = asset_data.get('lods', {})
    for index in range(1, len(lods.keys()) + 1):
        lod_file_path = lods.get(str(index))
        if asset_data.get('skeletal_mesh'):
            UnrealRemoteCalls.import_skeletal_mesh_lod(asset_data.get('asset_path'), lod_file_path, index)
        else:
            UnrealRemoteCalls.import_static_mesh_lod(asset_data.get('asset_path'), lod_file_path, index)


@track_progress(message='Setting lod build settings for "{attribute}"...', attribute='asset_path')
def set_lod_build_settings(asset_id, properties, property_data):
    """
    Sets the lod build settings.

    :param str asset_id: The unique id of the asset.
    :param PropertyData properties: A property data instance that contains all property values of the tool.
    :param dict property_data: A dictionary representation of the properties.
    """
    asset_data = properties.asset_data[asset_id]
    lods = asset_data.get('lods', {})
    for index in range(0, len(lods.keys()) + 1):
        if asset_data.get('skeletal_mesh'):
            UnrealRemoteCalls.set_skeletal_mesh_lod_build_settings(
                asset_data.get('asset_path'),
                index,
                property_data
            )
        else:
            UnrealRemoteCalls.set_static_mesh_lod_build_settings(
                asset_data.get('asset_path'),
                index,
                property_data
            )


def asset(properties):
    """
    Ingests an asset.

    :param PropertyData properties: A property data instance that contains all property values of the tool.
    """
    if properties.asset_data:
        property_data = settings.get_extra_property_group_data_as_dictionary(properties, only_key='unreal_type')

        # check path mode to see if exported assets should be imported to unreal
        if properties.path_mode in [
            PathModes.SEND_TO_PROJECT.value,
            PathModes.SEND_TO_DISK_THEN_PROJECT.value
        ]:
            for asset_data in properties.asset_data.values():
                # get the asset id
                asset_id = get_asset_id(asset_data.get('file_path'))

                # imports static mesh, skeletal mesh or animation
                import_asset(asset_id, properties, property_data)

                # import lods
                if asset_data.get('lods'):
                    reset_lods(asset_id, properties, property_data)
                    import_lod_files(asset_id, properties)
                    set_lod_build_settings(asset_id, properties, property_data)

                # import sockets
                if asset_data.get('sockets'):
                    create_static_mesh_sockets(asset_id, properties)
