# Copyright Epic Games, Inc. All Rights Reserved.

import re
import os
import bpy
from . import utilities, formatting, extension
from ..dependencies.unreal import UnrealRemoteCalls
from ..constants import BlenderTypes, PathModes, ToolInfo, Extensions, ExtensionTasks


class ValidationManager:
    """
    Handles the validation of assets.
    """

    def __init__(self, properties):
        self.properties = properties
        self.mesh_objects = utilities.get_from_collection(BlenderTypes.MESH, properties)
        self.rig_objects = utilities.get_from_collection(BlenderTypes.SKELETON, properties)
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

    def run(self):
        """
        Run the registered validations.
        """
        # run any pre validations defined in the extensions
        for attribute in dir(bpy.context.scene.send2ue.extensions):
            pre_validations = getattr(getattr(
                bpy.context.scene.send2ue.extensions, attribute, object),
                ExtensionTasks.PRE_VALIDATIONS.value,
                None
            )
            if pre_validations:
                if not pre_validations(self.properties):
                    return False

        # run the core validations
        for validator in self._validators:
            if not validator():
                return False

        # run any post validations defined in the extensions
        for attribute in dir(bpy.context.scene.send2ue.extensions):
            post_validations = getattr(getattr(
                bpy.context.scene.send2ue.extensions, attribute, object),
                ExtensionTasks.POST_VALIDATIONS.value,
                None
            )
            if post_validations:
                if not post_validations(self.properties):
                    return False

        return True

    @staticmethod
    def validate_collections_exist():
        """
        Checks the scene to make sure the appropriate collections exist.
        """
        for collection_name in ToolInfo.COLLECTION_NAMES.value:
            # throw an error if there is no collection with the given name
            if not bpy.data.collections.get(collection_name):
                utilities.report_error(
                    f'You do not have a collection "{collection_name}" in your outliner. Please create it.'
                )
                return False
        return True

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
                return False
        return True

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
                return False
        return True

    def validate_geometry_exists(self):
        """
        Checks the geometry of each object to see if it has vertices.
        """
        for mesh_object in self.mesh_objects:
            # check if vertices exist
            if len(mesh_object.data.vertices) <= 0:
                utilities.report_error(f'Mesh "{mesh_object.name}" has no geometry.')
                return False
        return True

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
                return False
        return True

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
                return False
        return True

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
                    'disk_animation_folder_path'
                ]
                for property_name in property_names:
                    error_message = formatting.auto_format_disk_folder_path(property_name, self.properties)
                    if error_message:
                        utilities.report_error(error_message)
                        return False
        return True

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
                    'unreal_animation_folder_path'
                ]
                for property_name in property_names:
                    error_message = formatting.auto_format_unreal_folder_path(property_name, self.properties)
                    if error_message:
                        utilities.report_error(error_message)
                        return False
        return True

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
                        return False
        return True

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
                            return False
        return True

    def validate_lod_names(self):
        """
        Checks each object to see if the name of the object matches the supplied regex expression.
        """
        if self.properties.import_lods:
            for mesh_object in self.mesh_objects:
                result = re.search(rf"({self.properties.lod_regex})", mesh_object.name)
                if not result:
                    utilities.report_error(
                        f'Object "{mesh_object.name}" does not follow the correct lod naming convention defined in the '
                        f'import setting by the lod regex.'
                    )
                    return False
        return True

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
                                    return False
        return True

    def validate_object_root_scale(self):
        """
        Checks the transforms on the provided object to see if they are applied.
        """
        if self.properties.validate_armature_transforms:
            for scene_object in self.rig_objects:
                non_zero_transforms = []

                # check the scale values
                if scene_object.scale[:] != (1.0, 1.0, 1.0):
                    non_zero_transforms.append(f'scale {scene_object.scale[:]}')

                if non_zero_transforms:
                    utilities.report_error(
                        f'"{scene_object.name}" has un-applied transforms "{", ".join(non_zero_transforms)}". These must '
                        f'be zero to avoid unexpected results. Otherwise, turn off this validation to ignore.'
                    )
                    return False
        return True

    def validate_required_unreal_plugins(self):
        """
        Checks whether the required unreal plugins are enabled.
        """
        missing_plugins = []

        if self.properties.import_grooms:
            # A dictionary of plugins where the key is the plugin name and value is the plugin label.
            groom_plugins = {
                'HairStrands': 'Groom',
                'AlembicHairImporter': 'Alembic Groom Importer'
            }
            missing_plugins += UnrealRemoteCalls.check_plugins(list(groom_plugins.keys()))

        plugin_names = ', '.join(groom_plugins[name] for name in missing_plugins)

        if missing_plugins:
            utilities.report_error(
                f'Please enable missing plugins in Unreal: {plugin_names}'
            )
            return False

        return True

    # TODO: temporary validation before lods support for groom is added
    def validate_groom_unsupported_lods(self):
        """
        Checks that import groom and import lods are not both selected.
        """
        if self.properties.import_lods and self.properties.import_grooms:
            utilities.report_error(
                'Groom LODs are currently unsupported at this time. Please disable either import LODs or import groom.'
            )
            return False
        return True
