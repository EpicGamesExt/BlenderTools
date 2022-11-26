# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
from send2ue.core.extension import ExtensionBase
from send2ue.core import utilities
from send2ue.constants import ToolInfo, AssetTypes


class UseFileNameAsFolder(ExtensionBase):
    name = 'use_file_name_as_folder'
    use_file_name_as_folder: bpy.props.BoolProperty(
        name="Use file name as folder",
        default=False,
        description=(
            "This uses the blend file name as a parent folder to contain sub-"
            "meshes in your unreal project"
        )
    )

    def pre_import(self, asset_data, properties):
        """
        Defines the pre import logic that uses blender collections as unreal folders

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.use_file_name_as_folder:
            asset_type = asset_data['_asset_type']
            if asset_type == AssetTypes.ANIMATION:
                object_name = asset_data['_armature_object_name']
                scene_object = bpy.data.objects.get(object_name)
                # update skeletal asset path now that it is under new collections path
                self.update_asset_data({
                    'skeleton_asset_path': utilities.get_skeleton_asset_path(
                        scene_object,
                        properties,
                        self.get_full_import_path
                    )
                })
            else:
                object_name = asset_data['_mesh_object_name']
                scene_object = bpy.data.objects.get(object_name)
                asset_name = utilities.get_asset_name(object_name, properties)
                # get import path when using blender collections as folders
                import_path = self.get_full_import_path(scene_object, properties, asset_type)

                self.update_asset_data({
                    'asset_folder': import_path,
                    'asset_path': f'{import_path}{asset_name}'
                })

    def get_full_import_path(self, scene_object, properties, asset_type):
        """
        Gets the unreal import path when use_file_name_as_folder extension is active.

        :param object scene_object: A object.
        :param object properties: The property group that contains variables that maintain the addon's correct state.
        :param str asset_type: The type of asset.
        :return str: The full import path for the given asset.
        """
        game_path = utilities.get_import_path(scene_object, properties, asset_type)
        file_name = bpy.path.display_name(bpy.context.blend_data.filepath)
        import_path = f'{game_path}{file_name}/'
        return import_path

    def draw_paths(self, dialog, layout, properties):
        """
        Draws an interface for the use_file_name_as_folder option under the paths tab.

        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        dialog.draw_property(self, layout, 'use_file_name_as_folder')
