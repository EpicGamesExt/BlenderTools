# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
import os
from . import utilities


class AffixApplicator:
    """
    Takes care of applying the asset name affixes or restoring the original names.
    """

    modified_objects: dict = {}

    def apply(self, properties):
        """
        Applies the defined affixes to the objects selected for export.

        :param object self: This refers the the AffixApplicator class instance.
        :param object properties: The property group that contains variables that maintain the addon's correct state.
        """
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


    def restore_original_names(self):
        """
        Restores the original names of to the objects from before the affixes have been applied.

        :param object self: This refers the the AffixApplicator class instance.
        """
        for object, original_name in self.modified_objects.items():
            object.name = original_name

            if(hasattr(object, "type") and object.type == 'IMAGE'):                
                self.rename_texture(object, original_name)


    def append_affix(self, object, affix, is_image=False):
        """
        Generates the renames where needed and appends it to the dict.

        :param object self: This refers the the AffixApplicator class instance.
        :param object object: The export object to be renamed with the affix added.
        :param str affix: The affix to either prepend or append, depending on whether it's a prefix or suffix.
        :param bool is_image: Indicates whether the object is an image.
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


    def prepare_textures(self, images, properties):
        """
        Prepares the textures by unpacking and renaming them for the export.
        
        :param object self: This refers the the AffixApplicator class instance.
        :param list images: A list of texture images referenced selected for export.
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
                    #file_paths.append(image.filepath_from_user())
                
            new_name = self.append_affix(image, properties.texture_name_affix, is_image=True)
            try:
                self.rename_texture(image, new_name)
            except FileExistsError as ex:
                errors.append(str(os.path.basename(ex.filename)))

        if errors:
            utilities.report_error("Failed to rename texture images because another file with the same name already exists!",
                ', '.join(errors))


    def rename_texture(self, image, new_name):
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
