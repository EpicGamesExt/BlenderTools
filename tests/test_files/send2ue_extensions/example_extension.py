# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
import os
from pprint import pprint
from send2ue.core.extension import ExtensionBase


class ExampleExtension(ExtensionBase):
    name = 'example'

    hello_property: bpy.props.StringProperty(default='Hello world')

    def draw_validations(self, dialog, layout):
        """
        Can be overridden to draw an interface for the extension under the validations tab.

        :param Send2UeSceneProperties self: The scene property group that contains all the addon properties.
        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        """
        row = layout.row()
        row.prop(self.extensions.example, 'hello_property')

    def pre_operation(self):
        """
        Defines the pre operation logic that will be run before the operation.

        :param Send2UeSceneProperties self: The scene property group that contains all the addon properties.
        """
        print('Before the Send to Unreal operation')
        self.unreal_mesh_folder_path = '/Game/example_extension/test/'
        self.unreal_animation_folder_path = '/Game/example_extension/test/animations'

    def pre_validations(self):
        """
        Defines the pre validation logic that will be an injected operation.

        :param Send2UeSceneProperties self: The scene property group that contains all the addon properties.
        """
        print('Before Validations')
        # Setting this to False will terminate execution in the validation phase
        if self.extensions.example.hello_property != 'Hello world':
            self.validations_passed = False

    def pre_mesh_export(self):
        """
        Defines the pre mesh export logic that will be an injected operation.

        :param PropertyGroup self: The scene property group that contains all the addon properties.
        """
        # the asset data using the current asset id
        asset_data = self.asset_data[self.asset_id]

        path, ext = os.path.splitext(asset_data.get('file_path'))
        asset_path = asset_data.get('asset_path')

        self.asset_data[self.asset_id]['file_path'] = f'{path}_added_this{ext}'
        self.asset_data[self.asset_id]['asset_path'] = f'{asset_path}_added_this'

        pprint(self.asset_data[self.asset_id])

    def pre_animation_export(self):
        """
        Defines the pre animation export logic that will be an injected operation.

        :param PropertyGroup self: The scene property group that contains all the addon properties.
        """
        print('Before Animation Export')
        asset_data = self.asset_data[self.asset_id]
        skeleton_asset_path = asset_data.get('skeleton_asset_path').replace('_Skeleton', '')

        self.asset_data[self.asset_id]['skeleton_asset_path'] = f'{skeleton_asset_path}_added_this_Skeleton'

        pprint(self.asset_data[self.asset_id])

    def post_operation(self):
        """
        Defines the post operation logic that will be run after the operation.
        """
        print('After the Send to Unreal operation')
