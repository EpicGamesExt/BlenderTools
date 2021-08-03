# Copyright Epic Games, Inc. All Rights Reserved.

import os
import shutil
import tempfile
from . import utilities


class AffixApplicator:
    """
    Takes care of applying the asset name affixes or restoring the original names.
    """

    def add_affixes(self, properties):
        """
        Adds the defined affixes to the objects selected for export.

        :param object self: This refers the the AffixApplicator class instance.
        :param object properties: The property group that contains variables that maintain the addon's correct state.
        """
        mesh_objects = utilities.get_from_collection(properties.mesh_collection_name, 'MESH', properties)
        rig_objects = utilities.get_from_collection(properties.rig_collection_name, 'ARMATURE', properties)
        is_skeletal_asset = bool(rig_objects)

        for mesh_object in mesh_objects:
            if len(mesh_object.modifiers) > 0:
                for modifier in mesh_object.modifiers:
                    if modifier.type == "ARMATURE":
                        if bool(modifier.object):
                            self.append_affix(mesh_object, properties.skeletal_mesh_name_affix)
                        else:
                            self.append_affix(mesh_object, properties.static_mesh_name_affix)
            else:
                self.append_affix(mesh_object, properties.static_mesh_name_affix)

            for slot in mesh_object.material_slots:
                self.append_affix(slot.material, properties.material_name_affix)

            texture_images = self.get_texture_images(mesh_object)
            self.rename_all_textures(texture_images, self.append_affix, properties)

        if is_skeletal_asset:
            actions = [utilities.get_actions(rig_object, properties.export_all_actions) for rig_object in
                       rig_objects]
            actions = [a for sublist in actions for a in sublist]  # flatten list
            for action in actions:
                self.append_affix(action, properties.animation_sequence_name_affix)

    def remove_affixes(self, properties):
        """
        Removes the defined affixes from the objects selected for export.

        :param object self: This refers the the AffixApplicator class instance.
        :param object properties: The property group that contains variables that maintain the addon's correct state.
        """
        mesh_objects = utilities.get_from_collection(properties.mesh_collection_name, 'MESH', properties)
        rig_objects = utilities.get_from_collection(properties.rig_collection_name, 'ARMATURE', properties)
        is_skeletal_asset = bool(rig_objects)
        max_strip=30

        print(mesh_objects)
        for mesh_object in mesh_objects:
            for i in range(max_strip):
                old_mesh_object_name = mesh_object.name
                self.discard_affix(mesh_object, properties.static_mesh_name_affix)
                self.discard_affix(mesh_object, properties.skeletal_mesh_name_affix)
                if old_mesh_object_name == mesh_object.name:
                    break

            for slot in mesh_object.material_slots:
                self.discard_affix(slot.material, properties.material_name_affix)

            texture_images = self.get_texture_images(mesh_object)
            self.rename_all_textures(texture_images, self.discard_affix, properties)

        if is_skeletal_asset:
            actions = [utilities.get_actions(rig_object, properties.export_all_actions) for rig_object in
                       rig_objects]
            actions = [a for sublist in actions for a in sublist]  # flatten list
            for action in actions:
                self.discard_affix(action, properties.animation_sequence_name_affix)

    @staticmethod
    def append_affix(scene_object, affix, is_image=False):
        """
        Generates the renames where needed and appends it to the dict.

        :param object scene_object: The export object to be renamed with the affix added.
        :param str affix: The affix to either prepend or append, depending on whether it's a prefix or suffix.
        :param bool is_image: Indicates whether the object is an image.
        :return str: The new object name.
        """
        filename, ext = os.path.splitext(scene_object.name)
        asset_name = filename if is_image else scene_object.name

        # Prefix
        if affix.endswith("_"):
            if scene_object.name.startswith(affix):
                return  # Do not add prefix when its already present
            scene_object.name = affix + asset_name + ext
        # Suffix
        else:
            if scene_object.name.endswith(affix):
                return  # Do not add suffix when its already present
            scene_object.name = asset_name + affix + ext

        return scene_object.name

    @staticmethod
    def discard_affix(scene_object, affix, is_image=False):
        """
        Generates the renames where needed and appends it to the dict.

        :param object scene_object: The export object to be renamed with the affix added.
        :param str affix: The affix to either prepend or append, depending on whether it's a prefix or suffix.
        :param bool is_image: Indicates whether the object is an image.
        :return str: The new object name.
        """
        filename, ext = os.path.splitext(scene_object.name)
        asset_name = filename if is_image else scene_object.name

        # Prefix
        if affix.endswith("_"):
            if scene_object.name.startswith(affix):
                scene_object.name = asset_name[len(affix):] + ext
        # Suffix
        else:
            if scene_object.name.endswith(affix):
                scene_object.name = asset_name[:-len(affix)] + ext

        return scene_object.name

    @staticmethod
    def get_texture_images(mesh_object):
        """
        This function iterates over all materials of the mesh object and returns the names of its textures.

        :param object mesh_object: A mesh object selected for export.
        :return list: A list of textures used in the materials.
        """
        images = []

        for material_slot in mesh_object.material_slots:
            if material_slot.material.node_tree:
                for node in material_slot.material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE':
                        images.append(node.image)

        return images

    def rename_all_textures(self, images, affix_operation, properties):
        """
        Prepares the textures by unpacking and renaming them for the export.

        :param list images: A list of texture images referenced selected for export.
        :param method affix_operation: The affix operation to run on the name, either appending or discarding the affix.
        :param object properties: The property group that contains variables that maintain the addon's correct state.
        :return list: A list of textures used in the materials.
        """

        errors = []

        for image in images:
            new_name = affix_operation(image, properties.texture_name_affix, is_image=True)
            try:
                self.rename_texture(image, new_name)
            except (FileExistsError, PermissionError) as ex:
                errors.append(str(ex))

        if errors:
            utilities.report_error(
                "Failed to rename the following texture images:",
                ', '.join(errors)
            )

    @staticmethod
    def rename_texture(image, new_name):
        """
        This function renames the texture object in blender and the referenced image file on the hard disk.

        :param object image: A texture image referenced selected for export.
        :param str new_name: New name for the texture including the affix.
        """
        if not new_name:
            return

        is_packed = image.source == 'FILE' and image.packed_file and not os.path.exists(image.filepath_from_user())
        if is_packed:
            image.unpack()

        path, filename = os.path.split(image.filepath_from_user())
        filename, ext = os.path.splitext(filename)

        if not new_name.endswith(ext):
            new_name = new_name + ext

        tempdir = tempfile.mkdtemp(prefix='Send2Unreal_')
        new_path = os.path.join(tempdir, new_name)

        shutil.move(image.filepath_from_user(), new_path)
        image.filepath = new_path

        if is_packed and os.path.exists(image.filepath_from_user()):
            utilities.remove_unpacked_files([image.filepath_from_user()])
