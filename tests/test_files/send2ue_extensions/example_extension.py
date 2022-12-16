# Copyright Epic Games, Inc. All Rights Reserved.

import os
import bpy
from pprint import pprint
from send2ue.core.extension import ExtensionBase
from send2ue.dependencies.unreal import remote_unreal_decorator


@remote_unreal_decorator
def rename_unreal_asset(source_asset_path, destination_asset_path):
    if unreal.EditorAssetLibrary.does_asset_exist(destination_asset_path):
        unreal.EditorAssetLibrary.delete_asset(destination_asset_path)
    return unreal.EditorAssetLibrary.rename_asset(source_asset_path, destination_asset_path)


class ExampleExtension(ExtensionBase):
    name = 'example'

    hello_property: bpy.props.StringProperty(default='Hello world')
    use_example_extension: bpy.props.BoolProperty(default=False)

    def draw_validations(self, dialog, layout, properties):
        """
        Can be overridden to draw an interface for the extension under the validations tab.

        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        row = layout.row()
        row.prop(self, 'use_example_extension')
        row.prop(self, 'hello_property')

    def pre_operation(self, properties):
        """
        Defines the pre operation task logic that will be run before the operation.

        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.use_example_extension:
            print('Before the Send to Unreal task')
            properties.unreal_mesh_folder_path = '/Game/example_extension/test/'
            properties.unreal_animation_folder_path = '/Game/example_extension/test/animations'

    def pre_validations(self, properties):
        """
        Defines the pre validation logic that will be an injected task.

        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.use_example_extension:
            print('Before Validations')
            # Setting this to False will terminate execution in the validation phase
            if self.hello_property != 'Hello world':
                return False
        return True

    def pre_mesh_export(self, asset_data, properties):
        """
        Defines the pre mesh export logic that will be an injected task.

        :param dict asset_data: A mutable dictionary of asset data for the current asset being processed.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.use_example_extension:
            # the asset data using the current asset id
            path, ext = os.path.splitext(asset_data['file_path'])
            asset_path = asset_data.get('asset_path')

            asset_data['file_path'] = f'{path}_added_this{ext}'
            asset_data['asset_path'] = f'{asset_path}_added_this'
            pprint(asset_data)
            self.update_asset_data(asset_data)

    def pre_animation_export(self, asset_data, properties):
        """
        Defines the pre animation export logic that will be an injected task.

        :param dict asset_data: A mutable dictionary of asset data for the current asset being processed.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.use_example_extension:
            print('Before Animation Export')
            skeleton_asset_path = asset_data.get('skeleton_asset_path').replace('_Skeleton', '')

            asset_data['skeleton_asset_path'] = f'{skeleton_asset_path}_added_this_Skeleton'
            pprint(asset_data)
            self.update_asset_data(asset_data)

    def post_import(self, asset_data, properties):
        """
        Defines the post import logic that will be an injected task.

        :param dict asset_data: A mutable dictionary of asset data for the current asset being processed.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.use_example_extension:
            print('After the import task')
            asset_path = asset_data.get('asset_path')
            if asset_path:
                rename_unreal_asset(asset_path, f'{asset_path}_renamed_again')

    def post_operation(self, properties):
        """
        Defines the post operation task that will be run after the operation.

        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.use_example_extension:
            print('After the Send to Unreal operation')
