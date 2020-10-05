# Copyright Epic Games, Inc. All Rights Reserved.
import bpy
import re
from . import utilities


def validate_collections_exist(properties):
    """
    This function checks the scene to make sure the appropriate collections exist.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return bool: True if all the collections exist.
    """
    error_message = []
    for collection_name in properties.collection_names:
        collection = bpy.data.collections.get(collection_name)
        # throw an error if there is no collection with the given name
        if not collection:
            error_message.append(
                f'You do not have a collection "{collection_name}" in your scene! Please create it!'
            )
    if error_message:
        utilities.report_error('\n'.join(error_message))
        return False

    return True


def validate_geometry_exists(mesh_objects):
    """
    This function checks the geometry of each object to see if it has vertices.

    :param mesh_objects: The list of mesh objects to be validated.
    :return bool: True if the objects passed the validation.
    """
    for mesh_object in mesh_objects:
        # check if vertices exist
        if len(mesh_object.data.vertices) <= 0:
            utilities.report_error(f'Mesh "{mesh_object.name}" has no geometry.')
            return False
    return True


def validate_disk_paths(properties):
    """
    This function checks each of the entered disk paths to see if they are correct.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return bool: True if the objects passed the validation.
    """
    error_message = []
    if properties.path_mode in ['export_to_disk', 'both']:
        if properties.incorrect_disk_mesh_folder_path:
            error_message.append(
                f'The mesh folder "{properties.disk_mesh_folder_path}" does not exist! '
                f'Please make sure that the path under "Mesh Folder (Disk)" was entered correctly!')

        if properties.incorrect_disk_animation_folder_path:
            error_message.append(
                f'The animation folder "{properties.disk_animation_folder_path}" does not exist! '
                f'Please make sure that the path under "Animation Folder (Disk)" was entered correctly!')

        if not bpy.data.filepath:
            error_message.append(
                f'"untitled" blend files are not supported! Please save your scene.')

    if error_message:
        utilities.report_error('\n'.join(error_message))
        return False

    return True


def validate_unreal_skeleton_path(unreal, properties):
    """
    This function checks to make sure this skeleton exists in unreal.

    :param object unreal: The unreal utilities module.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return bool: True if the objects passed the validation.
    """
    if properties.unreal_skeleton_asset_path:
        if not unreal.asset_exists(properties.unreal_skeleton_asset_path):
            utilities.report_error(
                f'There is no skeleton in your unreal project at: "{properties.unreal_skeleton_asset_path}".'
            )
            return False
    return True


def validate_geometry_materials(mesh_objects):
    """
    This function checks the geometry to see if the mesh has any unused materials.

    :param mesh_objects: The list of mesh objects to be validated
    :return bool: True if the objects passed the validation.
    """
    for mesh_object in mesh_objects:
        material_slots = [material_slots.name for material_slots in mesh_object.material_slots]

        if len(mesh_object.material_slots) > 0:
            # for each polygon check for its material index
            for polygon in mesh_object.data.polygons:
                material = mesh_object.material_slots[polygon.material_index].name
                if material in material_slots:
                    material_slots.remove(material)

                # remove used material names from the list of unused material names
                if material_slots:
                    for material_slot in material_slots:
                        utilities.report_error(f'Mesh "{mesh_object.name}" has a unused material "{material_slot}"')
                        return False
    return True


def validate_lod_names(mesh_objects):
    """
    This function checks each object to see if the name of the object matches the supplied regex expression.

    :param list mesh_objects: The list of mesh objects to be validated.
    :return bool: True if the objects passed the validation.
    """
    regex_expression = re.compile(r'(_LOD\d)')
    # check each obj in group
    for mesh_object in mesh_objects:
        # check if the meshes ending suffix contains its group name
        if not regex_expression.search(mesh_object.name):
            utilities.report_error(
                f'Object "{mesh_object.name}" does not follow the correct naming conventions for LODs.'
            )
            return False
    return True


def validate_texture_references(mesh_objects):
    """
    This function checks the geometry to see if the mesh has any materials with textures that have
    invalid references.

    :param list mesh_objects: The list of mesh objects to be validated.
    :return bool: True if the objects passed the validation.
    """
    for mesh_object in mesh_objects:
        # check each material slot on the mesh
        for material_slot in mesh_object.material_slots:
            # check each node in the material
            for node in material_slot.material.node_tree.nodes:
                # check to see if the material has an image
                if node.type == 'TEX_IMAGE':
                    if node.image:
                        try:
                            # check to see if the image reference works
                            node.image.update()
                        except RuntimeError:
                            utilities.report_error(
                                f'Mesh "{mesh_object.name}" has a material "{material_slot.material.name}" that '
                                f'contains a missing image "{node.image.name}".'
                            )
                            return False
    return True
