# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
import os
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
            if is_skeletal_asset:
                self.__append_affix(mesh_object, properties.skeletal_mesh_name_affix)
            else:
                self.__append_affix(mesh_object, properties.static_mesh_name_affix)

            for slot in mesh_object.material_slots:
                self.__append_affix(slot.material, properties.material_name_affix)

            texture_images = self.__get_texture_images(mesh_object)
            self.__rename_all_textures(texture_images, self.__append_affix, properties)

        if is_skeletal_asset:
            actions = [utilities.get_actions(rig_object, properties, properties.export_all_actions) for rig_object in rig_objects]
            actions = [a for sublist in actions for a in sublist] # flatten list
            for action in actions:
                self.__append_affix(action, properties.animation_sequence_name_affix)

    def remove_affixes(self, properties):
        """
        Removes the defined affixes from the objects selected for export.

        :param object self: This refers the the AffixApplicator class instance.
        :param object properties: The property group that contains variables that maintain the addon's correct state.
        """
        mesh_objects = utilities.get_from_collection(properties.mesh_collection_name, 'MESH', properties)
        rig_objects = utilities.get_from_collection(properties.rig_collection_name, 'ARMATURE', properties)
        is_skeletal_asset = bool(rig_objects)

        for mesh_object in mesh_objects:
            if is_skeletal_asset:
                self.__discard_affix(mesh_object, properties.skeletal_mesh_name_affix)
            else:
                self.__discard_affix(mesh_object, properties.static_mesh_name_affix)

            for slot in mesh_object.material_slots:
                self.__discard_affix(slot.material, properties.material_name_affix)

            texture_images = self.__get_texture_images(mesh_object)
            self.__rename_all_textures(texture_images, self.__discard_affix, properties)
        
        if is_skeletal_asset:
            actions = [utilities.get_actions(rig_object, properties, properties.export_all_actions) for rig_object in rig_objects]
            actions = [a for sublist in actions for a in sublist] # flatten list
            for action in actions:
                self.__discard_affix(action, properties.animation_sequence_name_affix)


    def __append_affix(self, object, affix, is_image=False):
        """
        Generates the renames where needed and appends it to the dict.

        :param object self: This refers the the AffixApplicator class instance.
        :param object object: The export object to be renamed with the affix added.
        :param str affix: The affix to either prepend or append, depending on whether it's a prefix or suffix.
        :param bool is_image: Indicates whether the object is an image.
        :return str: The new object name.
        """
        asset_name = os.path.splitext(object.name)[0] if is_image else object.name

        # Prefix
        if affix.endswith("_"):
            if object.name.startswith(affix):
                return  # Do not add prefix when its already present
            object.name = affix + asset_name
        # Suffix
        else:
            if object.name.endswith(affix):
                return  # Do not add suffix when its already present
            object.name = asset_name + affix

        return object.name


    def __discard_affix(self, object, affix, is_image=False):
        """
        Generates the renames where needed and appends it to the dict.

        :param object self: This refers the the AffixApplicator class instance.
        :param object object: The export object to be renamed with the affix added.
        :param str affix: The affix to either prepend or append, depending on whether it's a prefix or suffix.
        :param bool is_image: Indicates whether the object is an image.
        :return str: The new object name.
        """

        # Prefix
        if affix.endswith("_"):
            if object.name.startswith(affix):
                object.name = object.name[len(affix):]
        # Suffix
        else:
            if object.name.endswith(affix):
                object.name = object.name[:-len(affix)]

        return object.name
    

    def __get_texture_images(self, mesh_object):
        """
        This function iterates over all materials of the mesh object and returns the names of its textures.

        :param object self: This refers the the AffixApplicator class instance.
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


    def __rename_all_textures(self, images, affixOperation, properties):
        """
        Prepares the textures by unpacking and renaming them for the export.
        
        :param object self: This refers the the AffixApplicator class instance.
        :param list images: A list of texture images referenced selected for export.
        :param method affixOperation: The affix operation to run on the name, either appending or discarding the affix.
        :param object properties: The property group that contains variables that maintain the addon's correct state.
        :return list: A list of textures used in the materials.
        """

        errors = []
        
        for image in images:
            if image.source == 'FILE' and image.packed_file:
                # if the unpacked image does not exist on disk
                if not os.path.exists(image.filepath_from_user()):
                    # unpack the image
                    image.unpack()
                
            new_name = affixOperation(image, properties.texture_name_affix, is_image=True)
            try:
                self.__rename_texture(image, new_name)
            except (FileExistsError, PermissionError) as ex:
                print(str(ex))
                errors.append(str(os.path.basename(ex.filename)))

        if errors:
            utilities.report_error("Failed to rename the following texture images:",
                ', '.join(errors))


    def __rename_texture(self, image, new_name):
        """
        This function renames the texture object in blender and the referenced image file on the hard disk.

        :param object self: This refers the the AffixApplicator class instance.
        :param object image: A texture image referenced selected for export.
        :param str new_name: New name for the texture including the affix.
        """
        if not new_name:
            return

        current_path = image.filepath_from_user()
        path, filename = os.path.split(current_path)
        extension = os.path.splitext(filename)[1]
        new_path = os.path.join(path, new_name + extension)

        os.rename(current_path, new_path)
        image.filepath = new_path
