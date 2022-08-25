# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
from send2ue.core.extension import ExtensionBase
from send2ue.core import utilities
from send2ue.constants import ToolInfo, AssetTypes


class UseCollectionsAsFoldersExtension(ExtensionBase):
    name = 'use_collections_as_folders'
    use_collections_as_folders: bpy.props.BoolProperty(
        name="Use collections as folders",
        default=False,
        description=(
            "This uses the collection hierarchy in your scene as sub folders from "
            "the specified mesh folder in your unreal project"
        )
    )

    def pre_validations(self, properties):
        """
        Defines the pre validations logic that guarantees exclusive usage of some extensions.

        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.use_collections_as_folders:
            if properties.extensions.combine_meshes.combine_child_meshes:
                utilities.report_error(
                    f'Cannot use both combine meshes and use collections as folders extensions!'
                )
                return False
        return True

    def pre_import(self, asset_data, properties):
        """
        Defines the pre import logic that uses blender collections as unreal folders

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.use_collections_as_folders:
            if asset_data['_asset_type'] == AssetTypes.ANIMATION:
                game_path = properties.unreal_animation_folder_path
                object_name = asset_data['_armature_object_name']
            else:
                game_path = properties.unreal_mesh_folder_path
                object_name = asset_data['_mesh_object_name']

            asset_name = utilities.get_asset_name(object_name, properties)
            # get collections to be part of import path
            scene_object = bpy.data.objects.get(object_name)
            sub_path = self.get_collections_as_path(scene_object)
            path = f'{game_path}{sub_path}/'

            self.update_asset_data({
                'asset_folder': path,
                'asset_path': f'{path}{asset_name}'
            })

    def get_collections_as_path(self, scene_object):
        """
        Walks the collection hierarchy till it finds the given scene object.

        :param object scene_object: A object.
        :return str: The sub path to the given scene object.
        """
        parent_names = []
        if self.use_collections_as_folders and len(scene_object.users_collection) > 0:
            parent_collection = scene_object.users_collection[0]
            parent_names.append(parent_collection.name)
            self.set_parent_collection_names(parent_collection, parent_names)
            parent_names.reverse()
            return '/'.join(parent_names).replace(f'{ToolInfo.EXPORT_COLLECTION.value}/', '')

        return ''

    def set_parent_collection_names(self, collection, parent_names):
        """
        This function recursively adds the parent collection names to the given list until.

        :param object collection: A collection.
        :param list parent_names: A list of parent collection names.
        :return list: A list of parent collection names.
        """
        for parent_collection in bpy.data.collections:
            if collection.name in parent_collection.children.keys():
                parent_names.append(parent_collection.name)
                self.set_parent_collection_names(parent_collection, parent_names)
                return None

    def draw_paths(self, dialog, layout, properties):
        """
        Draws an interface for the use_collections_as_folders option under the paths tab.

        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        dialog.draw_property(self, layout, 'use_collections_as_folders')

