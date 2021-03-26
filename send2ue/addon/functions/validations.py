# Copyright Epic Games, Inc. All Rights Reserved.
import bpy
import re
import os
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
                f'You do not have a collection "{collection_name}" in your scene. Please create it.'
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

    if properties.path_mode in ['export_to_disk', 'both']:

        error_message = validate_disk_path_by_property(
            properties,
            "incorrect_disk_mesh_folder_path",
            True
        )
        if error_message:
            utilities.report_error(error_message)
            return False

        error_message = validate_disk_path_by_property(
            properties,
            "incorrect_disk_animation_folder_path",
            True
        )
        if error_message:
            utilities.report_error(error_message)
            return False

        error_message = validate_disk_path_by_property(
            properties,
            "mesh_folder_untitled_blend_file",
            True
        )
        if error_message:
            utilities.report_error(error_message)
            return False

        error_message = validate_disk_path_by_property(
            properties,
            "animation_folder_untitled_blend_file",
            True
        )
        if error_message:
            utilities.report_error(error_message)
            return False

    return True


def validate_disk_path_by_property(properties, property_name, detailed_message=False):
    """
    This function returns a validation message about the property passed in
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :param str property_name: Property Name to check
    :param bool detailed_message: Boolean to determine whether to return a detailed message
    :return str: The message from validation
    """

    message = ""
    if properties.path_mode in ['export_to_disk', 'both']:
        if property_name == "incorrect_disk_mesh_folder_path":
            if getattr(properties, property_name):
                message = f'The mesh folder "{properties.disk_mesh_folder_path}" does not exist. '

                if detailed_message:
                    message += f'Please make sure that the path under "Mesh Folder (Disk)" was entered correctly.'

            return message

        if property_name == "incorrect_disk_animation_folder_path":
            if getattr(properties, property_name):
                message = f'The animation folder "{properties.disk_animation_folder_path}" does not exist. '

                if detailed_message:
                    message += f'Please make sure that the path under "Animation Folder (Disk)" was entered correctly.'

            return message

        if property_name == "mesh_folder_untitled_blend_file":
            if getattr(properties, property_name):
                message = f'"untitled" blend files are not supported for relative paths. Please save your scene. '

                if detailed_message:
                    message += f'Please make sure that the path under "Mesh Folder (Disk)" was entered correctly.'

            return message

        if property_name == "animation_folder_untitled_blend_file":
            if getattr(properties, property_name):
                message = f'"untitled" blend files are not supported for relative paths. Please save your scene. '

                if detailed_message:
                    message += f'Please make sure that the path under "Animation Folder (Disk)" was entered correctly.'

            return message

    return message


def validate_unreal_paths(properties):
    """
    This function checks each of the entered unreal paths to see if they are
    correct.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return bool: True if the objects passed the validation.
    """

    if properties.path_mode in ['send_to_unreal', 'both']:
        error_message = validate_unreal_path_by_property(
            properties,
            "incorrect_unreal_mesh_folder_path",
            True
        )
        if error_message:
            utilities.report_error(error_message)
            return False

        error_message = validate_unreal_path_by_property(
            properties,
            "incorrect_unreal_animation_folder_path",
            True
        )
        if error_message:
            utilities.report_error(error_message)
            return False

        error_message = validate_unreal_path_by_property(
            properties,
            "incorrect_unreal_skeleton_path",
            True
        )
        if error_message:
            utilities.report_error(error_message)
            return False

    return True


def validate_unreal_path_by_property(properties, property_name, detailed_message=False):
    """
    This function returns a validation message about the property passed in
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :param str property_name: Property Name to check
    :param bool detailed_message: Boolean to determine whether to return a detailed message
    :return str: The message from validation
    """

    message = ""
    if properties.path_mode in ['send_to_unreal', 'both']:
        if property_name == "incorrect_unreal_mesh_folder_path":
            if getattr(properties, property_name):
                message = f'The mesh folder "{properties.unreal_mesh_folder_path}" needs to start with "/Game`". '

                if detailed_message:
                    message += f'Please make sure that the path under "Mesh Folder (Unreal)" was entered correctly.'

            return message

        if property_name == "incorrect_unreal_animation_folder_path":
            if getattr(properties, property_name):
                message = f'The animation folder "{properties.unreal_animation_folder_path}" needs to start with "/Game`". '

                if detailed_message:
                    message += f'Please make sure that the path under "Animation Folder (Unreal)" was entered correctly.'

            return message

        if property_name == "incorrect_unreal_skeleton_path":
            if getattr(properties, property_name):
                message = f'The skeleton asset name "{properties.unreal_skeleton_asset_path}" needs to start with "/Game`". '

                if detailed_message:
                    message += f'Please make sure that the path under "Skeleton Asset (Unreal)" was entered correctly.'

            return message

    return message


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

                # remove used material names from the list of unused material names
                if material in material_slots:
                    material_slots.remove(material)

            # iterate over unused materials and report about them
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
                    image = node.image
                    if image.source == 'FILE':
                        if not os.path.exists(image.filepath_from_user()):
                            utilities.report_error(
                                f'Mesh "{mesh_object.name}" has a material "{material_slot.material.name}" that '
                                f'contains a missing image "{node.image.name}".'
                            )
                            return False
    return True
