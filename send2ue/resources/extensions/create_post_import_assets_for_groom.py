# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
from send2ue.core.extension import ExtensionBase
from send2ue.core import utilities
from send2ue.constants import UnrealTypes
from send2ue.dependencies.unreal import UnrealRemoteCalls


class CreatePostImportAssetsForGroom(ExtensionBase):
    name = 'create_post_import_assets_for_groom'

    binding_asset: bpy.props.BoolProperty(
        name="Groom binding asset",
        default=True,
        description=(
            "This creates a binding asset for the imported groom asset and associated mesh asset."
        )
    )

    blueprint_with_groom: bpy.props.BoolProperty(
        name="Blueprint asset with groom component",
        default=False,
        description=(
            'This creates a blueprint asset with groom components from the imported groom assets parented under'
            'their associated skeletal mesh from the same import.'
        )
    )

    def pre_validations(self, properties):
        """
        Defines the pre validations logic that checks whether create binding asset is on if create blueprint with groom
        is checked.

        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.blueprint_with_groom:
            if not self.binding_asset:
                utilities.report_error(
                    f'Cannot create blueprint asset with groom if not creating binding asset!'
                )
                return False
        return True

    def post_import(self, asset_data, properties):
        """
        Defines the post import logic for creating post import assets for the current groom asset.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if asset_data.get('_asset_type') == UnrealTypes.GROOM:
            if self.binding_asset and properties.import_meshes:
                binding_asset_path = None
                # get the mesh asset data related to this groom asset data
                mesh_asset_data = utilities.get_related_mesh_asset_data_from_groom_asset_data(asset_data)
                groom_asset_path = asset_data.get('asset_path', '')
                mesh_asset_path = mesh_asset_data.get('asset_path', '')

                if not UnrealRemoteCalls.asset_exists(groom_asset_path):
                    return

                # don't create a binding asset if the mesh doesn't exist. This happens in a groom only export
                if not UnrealRemoteCalls.asset_exists(mesh_asset_path):
                    return

                if groom_asset_path and mesh_asset_path:
                    binding_asset_path = UnrealRemoteCalls.create_binding_asset(groom_asset_path, mesh_asset_path)

                if self.blueprint_with_groom and binding_asset_path:
                    UnrealRemoteCalls.create_blueprint_with_groom(groom_asset_path, mesh_asset_path, binding_asset_path)

    def draw_import(self, dialog, layout, properties):
        """
        Draws an interface for the create_post_import_assets_for_groom extension in the import tab.

        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        box = layout.box()
        box.label(text='Create post-import assets for groom:')
        dialog.draw_property(self, box, 'binding_asset')
        dialog.draw_property(self, box, 'blueprint_with_groom')
