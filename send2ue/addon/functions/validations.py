# Copyright Epic Games, Inc. All Rights Reserved.
import bpy
import re
import os
from . import utilities, unreal


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


def validate_object_names(mesh_objects, rig_objects):
    """
    This function checks each object for invalid names.

    :param list mesh_objects: The list of mesh objects to be validated.
    :param list rig_objects: The list of armature objects to be validated.
    :return bool: True if the objects passed the validation.
    """
    for scene_object in mesh_objects + rig_objects:
        # check if the object name is none
        if scene_object.name.lower() in ['none']:
            utilities.report_error(
                f'Object "{scene_object.name}" has an invalid name. Please rename it.'
            )
            return False
    return True


def validate_scene_units(properties):
    """
    This function checks that the unit settings are correct.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return bool: True if the objects passed the validation.
    """
    if properties.validate_unit_settings:
        unit_settings = bpy.context.scene.unit_settings
        if unit_settings.system != 'METRIC':
            utilities.report_error(
                f'"{unit_settings.system}" unit system is not recommended. Please change to "METRIC", or disable '
                f'this validation.'
            )
            return False

        if round(unit_settings.scale_length, 2) != 1.00:
            utilities.report_error(
                f'Unit scale {round(unit_settings.scale_length, 2)} is not recommended. Please change to 1.0, '
                f'or disable this validation.'
            )
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


def validate_unreal_skeleton_path(rig_objects, mesh_objects, properties):
    """
    This function checks each if the unreal skeleton path is correct.

    :param list rig_objects: A list of armature objects.
    :param list mesh_objects: A list of mesh objects.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return bool: True if the objects passed the validation.
    """
    properties.incorrect_unreal_skeleton_path = False
    if not mesh_objects:
        if properties.path_mode in ['send_to_unreal', 'both']:
            for rig_object in rig_objects:
                skeleton_path = utilities.get_skeleton_game_path(rig_object, properties)
                if not unreal.asset_exists(skeleton_path):
                    properties.incorrect_unreal_skeleton_path = True
                    error_message = validate_unreal_skeleton_path_property(
                        properties,
                        "incorrect_unreal_skeleton_path",
                        False,
                        skeleton_path=skeleton_path
                    )
                    if error_message:
                        utilities.report_error(error_message)
                        return False

    return True


def validate_unreal_skeleton_path_property(properties, property_name, detailed_message=False, skeleton_path=None):
    """
    This function returns a validation message about the unreal skeleton path.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :param str property_name: Property Name to check
    :param bool detailed_message: Boolean to determine whether to return a detailed message
    :param str skeleton_path: The skeleton path to display in the message.
    :return str: The message from validation
    """
    message = ""
    if not skeleton_path:
        skeleton_path = properties.unreal_skeleton_asset_path

    if getattr(properties, property_name):
        message = f'The skeleton asset "{skeleton_path}" does not exist in unreal.'

        if detailed_message:
            message += f' Please make sure that the path under "Skeleton Asset (Unreal)" was entered correctly.'

    return message


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
            return validate_unreal_skeleton_path_property(
                properties,
                property_name,
                detailed_message=detailed_message,

            )

    return message


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


def validate_applied_armature_scale(scene_objects):
    """
    This function checks the transforms on the provided object to see if they are applied.

    :param list scene_objects: A list of objects to be validated.
    :return bool: True if the objects passed the validation.
    """
    for scene_object in scene_objects:
        non_zero_transforms = []

        # check the scale values
        if scene_object.scale[:] != (1.0, 1.0, 1.0):
            non_zero_transforms.append(f'scale {scene_object.scale[:]}')

        # check the scale values
        if scene_object.location[:] != (0.0, 0.0, 0.0):
            non_zero_transforms.append(f'location {scene_object.location[:]}')

        # check the rotation values of the active rotation mode
        if scene_object.rotation_mode in ['XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX']:
            if scene_object.rotation_euler[:] != (0.0, 0.0, 0.0):
                rotation_euler = utilities.get_transform_in_degrees(scene_object.rotation_euler[:])
                non_zero_transforms.append(f'rotation_euler {rotation_euler}')

        if scene_object.rotation_mode == 'QUATERNION':
            if scene_object.rotation_quaternion[:] != (1.0, 0.0, 0.0, 0.0):
                rotation_quaternion = utilities.get_transform_in_degrees(scene_object.rotation_quaternion[:])
                non_zero_transforms.append(f'rotation_quaternion {rotation_quaternion}')

        if scene_object.rotation_mode == 'AXIS_ANGLE':
            if scene_object.rotation_axis_angle[:] != (0.0, 0.0, 1.0, 0.0):
                rotation_axis_angle = utilities.get_transform_in_degrees(scene_object.rotation_axis_angle[:])
                non_zero_transforms.append(f'rotation_axis_angle {rotation_axis_angle}')

        if non_zero_transforms:
            utilities.report_error(
                f'"{scene_object.name}" has un-applied transforms "{", ".join(non_zero_transforms)}". These must '
                f'be zero to avoid unexpected results. Otherwise, turn off this validation to ignore.'
            )
            return False
    return True


def validate_file_permissions(folder_path, properties, ui=False):
    """
    This function checks the file permissions of the given folder.

    :param str folder_path: A path to a folder on disk.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :param bool ui: Whether or not the is used in a ui.
    :return bool: True if the objects passed the validation.
    """
    full_path = os.path.join(folder_path, 'test.txt')
    if properties.path_mode in ['export_to_disk', 'both']:
        if os.path.exists(folder_path):
            try:
                with open(full_path, 'w') as test:
                    test.write('test')
            except PermissionError:
                message = f'The permissions of "{folder_path}" will not allow files to write to it.'
                if ui:
                    return message
                else:
                    utilities.report_error(message)
                    return False

    if os.path.exists(full_path):
        os.remove(full_path)

    return True


def show_asset_affix_message(properties, property_name):
    """
    This function returns a validation message about the affix property passed in.

    :param object properties: The property group that contains variables that maintain the addons correct state.
    :param str property_name: Property name to check
    :return str: The message from validation
    """

    message = ""
    invalid_affix = getattr(properties, property_name)

    if invalid_affix:
        message = (
            'The affix must not be empty and either start or end with an underscore _ character '
            '(e.g. Prefix_ or _Suffix).'
        )

    return message


def validate_asset_affixes(self, context):
    """
    This function is called every time the unreal affix text field is updated.

    :param object self: This is a reference to the property group class this functions in appended to.
    :param object value: The value of the property group class this update function is assigned to.
    """

    self.incorrect_static_mesh_name_affix = is_invalid_asset_affix_format(self.static_mesh_name_affix)
    self.incorrect_texture_name_affix = is_invalid_asset_affix_format(self.texture_name_affix)
    self.incorrect_material_name_affix = is_invalid_asset_affix_format(self.material_name_affix)
    self.incorrect_skeletal_mesh_name_affix = is_invalid_asset_affix_format(self.skeletal_mesh_name_affix)
    self.incorrect_animation_sequence_name_affix = is_invalid_asset_affix_format(self.animation_sequence_name_affix)


def is_invalid_asset_affix_format(affix_value):
    """
    Checks whether the given value is an invalid asset name affix.

    :param str affix_value: The value of the affix.
    """

    is_empty = not affix_value
    no_underscore = not affix_value.startswith("_") and not affix_value.endswith("_")
    both_underscores = affix_value.startswith("_") and affix_value.endswith("_")

    return is_empty or no_underscore or both_underscores
