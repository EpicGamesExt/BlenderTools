# Copyright Epic Games, Inc. All Rights Reserved.

import re
import os
import bpy
from . import utilities, formatting
from ..dependencies.unreal import UnrealRemoteCalls
from ..constants import AssetTypes, PathModes, ToolInfo, Extensions, ExtensionOperators


class ValidationManager:
    """
    Handles the validation of assets.
    """

    def __init__(self, properties):
        self.properties = properties
        self.mesh_objects = utilities.get_from_collection(AssetTypes.MESH, properties)
        self.rig_objects = utilities.get_from_collection(AssetTypes.SKELETON, properties)
        self._validators = []
        self._register_validators()

    def _register_validators(self):
        """
        Registers all method in this class that start with `validate`.
        """
        for attribute in dir(self):
            if attribute.startswith('validate_'):
                validator = getattr(self, attribute)
                self._validators.append(validator)

        # add in any validations defined in the extensions
        operator_namespace = getattr(bpy.ops, ToolInfo.NAME.value, None)
        if operator_namespace:
            for attribute in dir(operator_namespace):
                if attribute.startswith(f'{Extensions.NAME}_'):
                    validation_operator = getattr(operator_namespace, attribute)
                    if attribute.endswith(f'_{ExtensionOperators.PRE_VALIDATIONS.value}'):
                        self._validators.insert(0, validation_operator)
                    if attribute.endswith(f'_{ExtensionOperators.POST_VALIDATIONS.value}'):
                        self._validators.append(validation_operator)

    def run(self):
        """
        Run the registered validations.
        """
        self.properties.validations_passed = True
        for validator in self._validators:
            if self.properties.validations_passed:
                validator()
            else:
                return False
        return True

    def validate_collections_exist(self):
        """
        Checks the scene to make sure the appropriate collections exist.
        """
        for collection_name in ToolInfo.COLLECTION_NAMES.value:
            # throw an error if there is no collection with the given name
            if not bpy.data.collections.get(collection_name):
                utilities.report_error(
                    f'You do not have a collection "{collection_name}" in your outliner. Please create it.'
                )
                self.properties.validations_passed = False

    def validate_asset_data_exists(self):
        """
        Checks that there is data to export.
        """
        if self.properties.path_mode in [
            PathModes.SEND_TO_PROJECT.value,
            PathModes.SEND_TO_DISK_THEN_PROJECT.value,
            PathModes.SEND_TO_DISK.value
        ]:
            if not self.mesh_objects + self.rig_objects:
                utilities.report_error(
                    f'You do not have any objects under the "{ToolInfo.EXPORT_COLLECTION.value}" collection!'
                )
                self.properties.validations_passed = False

    def validate_object_names(self):
        """
        Checks each object for invalid names.
        """
        for scene_object in self.mesh_objects + self.rig_objects:
            # check if the object name is none
            if scene_object.name.lower() in ['none']:
                utilities.report_error(
                    f'Object "{scene_object.name}" has an invalid name. Please rename it.'
                )
                self.properties.validations_passed = False

    def validate_geometry_exists(self):
        """
        Checks the geometry of each object to see if it has vertices.
        """
        for mesh_object in self.mesh_objects:
            # check if vertices exist
            if len(mesh_object.data.vertices) <= 0:
                utilities.report_error(f'Mesh "{mesh_object.name}" has no geometry.')
                self.properties.validations_passed = False

    def validate_scene_scale(self):
        """
        Checks that the unit scale is correct.
        """
        if self.properties.validate_scene_scale != 'off':
            length_unit = str(round(bpy.context.scene.unit_settings.scale_length, 3))
            if length_unit != self.properties.validate_scene_scale:
                utilities.report_error(
                    f'The scene scale "{length_unit}" is not recommended. Please change to '
                    f'"{self.properties.validate_scene_scale}", or disable this validation.'
                )
                self.properties.validations_passed = False

    def validate_scene_frame_rate(self):
        """
        Checks that the frame rate is correct.
        """
        if self.properties.validate_time_units != 'off':
            time_unit = str(bpy.context.scene.render.fps)
            if time_unit != self.properties.validate_time_units:
                utilities.report_error(
                    f'The frame rate "{time_unit}" is not recommended. Please change to '
                    f'"{self.properties.validate_time_units}" in your render settings before continuing, '
                    f'or disable this validation.'
                )
                self.properties.validations_passed = False

    def validate_disk_folders(self):
        """
        Checks each of the entered disk folder paths to see if they are
        correct.
        """
        if self.properties.validate_paths:
            if self.properties.path_mode in [
                PathModes.SEND_TO_DISK.value,
                PathModes.SEND_TO_DISK_THEN_PROJECT.value
            ]:
                property_names = [
                    'disk_mesh_folder_path',
                    'disk_animation_folder_path',
                    'disk_collision_folder_path'
                ]
                for property_name in property_names:
                    error_message = formatting.auto_format_disk_folder_path(property_name, self.properties)
                    if error_message:
                        utilities.report_error(error_message)
                        self.properties.validations_passed = False
                        return

    def validate_unreal_folders(self):
        """
        Checks each of the unreal folder paths to see if they are correct.
        """
        if self.properties.validate_paths:
            if self.properties.path_mode in [
                PathModes.SEND_TO_PROJECT.value,
                PathModes.SEND_TO_DISK_THEN_PROJECT.value
            ]:
                property_names = [
                    'unreal_mesh_folder_path',
                    'unreal_animation_folder_path',
                    'unreal_collision_folder_path',
                ]
                for property_name in property_names:
                    error_message = formatting.auto_format_unreal_folder_path(property_name, self.properties)
                    if error_message:
                        utilities.report_error(error_message)
                        self.properties.validations_passed = False
                        return

    def validate_unreal_asset_paths(self):
        """
        Checks each of the entered unreal asset paths to see if they are
        correct.
        """
        if self.properties.validate_paths:
            if self.properties.path_mode in [
                PathModes.SEND_TO_PROJECT.value,
                PathModes.SEND_TO_DISK_THEN_PROJECT.value
            ]:
                property_names = [
                    'unreal_skeleton_asset_path',
                    'unreal_physics_asset_path',
                    'unreal_skeletal_mesh_lod_settings_path',
                ]
                for property_name in property_names:
                    error_message = formatting.auto_format_unreal_asset_path(property_name, self.properties)
                    if error_message:
                        utilities.report_error(error_message)
                        self.properties.validations_passed = False
                        return

    def validate_materials(self):
        """
        Checks to see if the mesh has any unused materials.
        """
        if self.properties.validate_materials:
            for mesh_object in self.mesh_objects:
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
                            self.properties.validations_passed = False
                            return

    def validate_lod_names(self):
        """
        Checks each object to see if the name of the object matches the supplied regex expression.
        """
        if self.properties.import_lods:
            for mesh_object in self.mesh_objects:
                result = re.search(rf"({self.properties.lod_regex})", mesh_object.name)
                if not result:
                    utilities.report_error(
                        f'Object "{mesh_object.name}" does not follow the correct lod naming convention defined in the'
                        f'import setting by the lod regex.'
                    )
                    self.properties.validations_passed = False
                    return

    def validate_texture_references(self):
        """
        Checks to see if the mesh has any materials with textures that have
        invalid references.
        """
        if self.properties.validate_textures:
            for mesh_object in self.mesh_objects:
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
                                    self.properties.validations_passed = False
                                    return

    def validate_object_root_orientation(self):
        """
        Checks the transforms on the provided object to see if they are applied.
        """
        for scene_object in self.rig_objects:
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
                self.properties.validations_passed = False
                return
