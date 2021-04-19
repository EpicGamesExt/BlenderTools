# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
import os
from . import utilities


class AffixApplicator:

    modified_objects: dict = {}

    def apply(self, properties):
        self.modified_objects.clear()

        mesh_objects = utilities.get_from_collection(properties.mesh_collection_name, 'MESH', properties)
        rig_objects = utilities.get_from_collection(properties.rig_collection_name, 'ARMATURE', properties)
        is_skeletal_asset = bool(rig_objects)

        for mesh_object in mesh_objects:
            if is_skeletal_asset:
                self.append_affix(mesh_object, properties.skeletal_mesh_name_affix)
            else:
                self.append_affix(mesh_object, properties.static_mesh_name_affix)

            for slot in mesh_object.material_slots:
                self.append_affix(slot.material, properties.material_name_affix)

            texture_images = self.get_texture_images(mesh_object)
            self.prepare_textures(texture_images, properties)


    def revert(self):
        for object, original_name in self.modified_objects.items():
            object.name = original_name

            if(hasattr(object, "type") and object.type == 'IMAGE'):                
                self.rename_texture(object, original_name)

    def append_affix(self, object, affix, is_image=False):
        """
        Generates the renames where needed and appends it to the dict.

        :param dict renames: Dictionary containing all the renames that should be executed after the export.
        :param str game_path: The game path for the export.
        :param str asset_name: The name of the asset to export.
        :param str affix: The affix to either prepend or append, depending on whether it's a prefix or suffix.
        :param str removeDefaultAffix: A default affix that has to be removed from the asset name.
        """        
        asset_name = os.path.splitext(object.name)[0] if is_image else object.name

        # Store original name so we can restore it after the export
        self.modified_objects[object] = asset_name

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
    

    def get_texture_images(self, mesh_object):
        """
        This function iterates over all materials of the mesh object and returns the names of its textures.

        :return list: A list of textures used in the materials.
        """
        images = []

        for material_slot in mesh_object.material_slots:
            if material_slot.material.node_tree:
                for node in material_slot.material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE':
                        images.append(node.image)
        
        return images


    def prepare_textures(self, images, properties):
        """
        This function iterates over all materials of the mesh object and returns the names of its textures.

        :return list: A list of textures used in the materials.
        """
        
        for image in images:
            if image.source == 'FILE' and image.packed_file:
                # if the unpacked image does not exist on disk
                if not os.path.exists(image.filepath_from_user()):
                    # unpack the image
                    image.unpack()
                    #file_paths.append(image.filepath_from_user())
                
            new_name = self.append_affix(image, properties.texture_name_affix, is_image=True)
            self.rename_texture(image, new_name)
    
    def rename_texture(self, image, new_name):
        if not new_name:
            return

        current_path = image.filepath_from_user()
        path, filename = os.path.split(current_path)
        extension = os.path.splitext(filename)[1]
        new_path = os.path.join(path, new_name + extension)

        os.rename(current_path, new_path)
        image.filepath = new_path
