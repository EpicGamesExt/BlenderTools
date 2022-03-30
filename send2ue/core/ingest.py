# Copyright Epic Games, Inc. All Rights Reserved.

from . import settings
from ..constants import PathModes
from ..dependencies.unreal import UnrealRemoteCalls
from .utilities import track_progress


@track_progress(message='Importing asset "{param}"...', param='file_path')
def import_asset(file_path, asset_data, property_data):
    """
    Imports an asset to unreal based on the asset data in the provided dictionary.

    :param str file_path: The full path to the file to import.
    :param dict asset_data: A dictionary of import parameters.
    :param dict property_data: A dictionary representation of the properties.
    """
    try:
        UnrealRemoteCalls.import_asset(file_path, asset_data, property_data)
    except TimeoutError:
        print("Got a timeout on probable large asset, continuing ...")


@track_progress(message='Importing fcurves on "{param}"...', param='asset_path')
def import_animation_fcurves(asset_path, fcurve_file_path):
    """
    Imports fcurves from a file onto an animation sequence.

    :param str asset_path: The project path to the skeletal mesh in unreal.
    :param str fcurve_file_path: The file path to the fcurve file.
    """
    UnrealRemoteCalls.import_animation_fcurves(asset_path, fcurve_file_path)


@track_progress(message='Importing skeletal mesh "{param}"...', param='file_path')
def import_skeletal_mesh_lod(asset_path, file_path, index):
    """
    Imports a lod onto a skeletal mesh.

    :param str asset_path: The project path to the skeletal mesh in unreal.
    :param str file_path: The path to the fbx file that contains the lods on disk.
    :param int index: Which lod index to import the lod on.
    """
    UnrealRemoteCalls.import_skeletal_mesh_lod(asset_path, file_path, index)


@track_progress(message='Importing static mesh "{param}"...', param='file_path')
def import_static_mesh_lod(asset_path, file_path, index):
    """
    Imports a lod onto a static mesh.

    :param str asset_path: The project path to the skeletal mesh in unreal.
    :param str file_path: The path to the fbx file that contains the lods on disk.
    :param int index: Which lod index to import the lod on.
    """
    UnrealRemoteCalls.import_static_mesh_lod(asset_path, file_path, index)


@track_progress(message='Setting skeletal mesh lod build settings for "{param}"...', param='asset_path')
def set_skeletal_mesh_lod_build_settings(asset_path, index, properties):
    """
    Sets the lod build settings for skeletal mesh.

    :param str asset_path: The project path to the skeletal mesh in unreal.
    :param int index: Which lod index to import the lod on.
    :param PropertyData properties: A property data instance that contains all property values of the tool.
    """
    UnrealRemoteCalls.set_skeletal_mesh_lod_build_settings(asset_path, index, properties)


@track_progress(message='Setting static mesh lod build settings for "{param}"...', param='asset_path')
def set_static_mesh_lod_build_settings(asset_path, index, properties):
    """
    Sets the lod build settings for static mesh.

    :param str asset_path: The project path to the static mesh in unreal.
    :param int index: Which lod index to import the lod on.
    :param PropertyData properties: A property data instance that contains all property values of the tool.
    """
    UnrealRemoteCalls.set_static_mesh_lod_build_settings(asset_path, index, properties)


@track_progress(message='Resetting static mesh lods for "{param}"...', param='asset_path')
def reset_static_mesh_lods(asset_path):
    """
    Removes all lods on the given static mesh.

    :param str asset_path: The project path to the static mesh in unreal.
    """
    UnrealRemoteCalls.reset_static_mesh_lods(asset_path)


@track_progress(message='Resetting skeletal mesh lods for "{param}"...', param='asset_path')
def reset_skeletal_mesh_lods(asset_path, property_data):
    """
    Removes all lods on the given skeletal mesh.

    :param str asset_path: The project path to the skeletal mesh in unreal.
    :param dict property_data: A dictionary representation of the properties.
    """
    UnrealRemoteCalls.reset_skeletal_mesh_lods(asset_path, property_data)


@track_progress(message='Creating static mesh sockets for "{param}"...', param='asset_path')
def create_static_mesh_sockets(asset_path, asset_data):
    """
    Creates sockets on a static mesh.

    :param str asset_path: The project path to the static mesh in unreal.
    :param dict asset_data: A dictionary of import parameters.
    """
    UnrealRemoteCalls.set_static_mesh_sockets(asset_path, asset_data)


@track_progress(message='Setting static mesh collision for "{param}"...', param='asset_path')
def set_static_mesh_collision(asset_path, collision_asset_path):
    """
    Sets the complex collision on a static mesh.

    :param str asset_path: The project path to the static mesh in unreal.
    :param str collision_asset_path: The project path to the collision mesh in unreal.
    """
    UnrealRemoteCalls.set_static_mesh_collision(asset_path, collision_asset_path)


def reset_lods(asset_data, property_data):
    """
    Removes all lods on the given mesh.

    :param dict asset_data: A dictionary of import parameters.
    :param dict property_data: A dictionary representation of the properties.
    """
    if asset_data.get('skeletal_mesh'):
        reset_skeletal_mesh_lods(asset_data.get('asset_path'), property_data)
    else:
        reset_static_mesh_lods(asset_data.get('asset_path'))


def import_lod_files(asset_data):
    """
    Imports lods onto a mesh.

    :param dict asset_data: A dictionary of import parameters.
    """
    lods = asset_data.get('lods', {})
    for index in range(1, len(lods.keys()) + 1):
        lod_file_path = lods.get(str(index))
        if asset_data.get('skeletal_mesh'):
            import_skeletal_mesh_lod(asset_data.get('asset_path'), lod_file_path, index)
        else:
            import_static_mesh_lod(asset_data.get('asset_path'), lod_file_path, index)


def set_lod_build_settings(asset_data, property_data):
    """
    Sets the lod build settings.

    :param dict asset_data: A dictionary of import parameters.
    :param dict property_data: A dictionary representation of the properties.
    """
    lods = asset_data.get('lods', {})
    for index in range(0, len(lods.keys()) + 1):
        if asset_data.get('skeletal_mesh'):
            set_skeletal_mesh_lod_build_settings(
                asset_data.get('asset_path'),
                index,
                property_data
            )
        else:
            set_static_mesh_lod_build_settings(
                asset_data.get('asset_path'),
                index,
                property_data
            )


def asset(assets_data, properties):
    """
    Ingests an asset.

    :param list[dict] assets_data: A list of dictionaries of import parameters.
    :param PropertyData properties: A property data instance that contains all property values of the tool.
    """
    # if exporting a static mesh, skeletal mesh or animation
    if assets_data:
        property_data = settings.get_extra_property_group_data_as_dictionary(properties, only_key='unreal_type')

        # check path mode to see if exported assets should be imported to unreal
        if properties.path_mode in [
            PathModes.SEND_TO_PROJECT.value,
            PathModes.SEND_TO_DISK_THEN_PROJECT.value
        ]:
            for asset_data in assets_data:
                import_asset(asset_data.get('file_path'), asset_data, property_data)

                # import lods
                if asset_data.get('lods'):
                    reset_lods(asset_data, property_data)
                    import_lod_files(asset_data)
                    set_lod_build_settings(asset_data, property_data)

                # import sockets
                if asset_data.get('sockets'):
                    create_static_mesh_sockets(asset_data.get('asset_path'), asset_data)

                # import collisions
                collision = asset_data.get('collision')
                if collision:
                    property_data.update({
                        'import_materials': {'value': False},
                        'import_textures': {'value': False},
                    })
                    import_asset(collision.get('file_path'), collision, property_data)
                    set_static_mesh_collision(asset_data.get('asset_path'), collision.get('asset_path'))

                # import fcurves
                fcurve_file_path = asset_data.get('fcurve_file_path')
                if fcurve_file_path:
                    import_animation_fcurves(asset_data.get('asset_path'), fcurve_file_path)
