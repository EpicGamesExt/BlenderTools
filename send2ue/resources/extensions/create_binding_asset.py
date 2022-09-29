# Copyright Epic Games, Inc. All Rights Reserved.

import os
import bpy
from send2ue.core.extension import ExtensionBase
from send2ue.core import export, settings
from send2ue.dependencies.unreal import UnrealRemoteCalls


class CreateBindingAsset(ExtensionBase):
    name = 'create_binding_asset'

    create_binding_asset: bpy.props.BoolProperty(
        name="Create binding asset",
        default=True,
        description=(
            "This creates a binding asset for the imported groom asset and associated mesh asset."
        )
    )

    def post_import(self, asset_data, properties):
        """
        Defines the post import logic for creating a binding asset for the current groom asset.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.create_binding_asset and asset_data.get('groom') and properties.import_meshes:
            groom_asset_path = asset_data.get('asset_path')
            mesh_asset_path = asset_data.get('mesh_asset_path')
            if groom_asset_path and mesh_asset_path:
                UnrealRemoteCalls.create_binding_asset(groom_asset_path, mesh_asset_path)

    def draw_import(self, dialog, layout, properties):
        """
        Draws an interface for the create_binding_asset extension in the import tab.

        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        dialog.draw_property(self, layout, 'create_binding_asset')
