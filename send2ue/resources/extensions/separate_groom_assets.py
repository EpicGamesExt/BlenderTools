# Copyright Epic Games, Inc. All Rights Reserved.

import os
import bpy
from send2ue.core.extension import ExtensionBase
from send2ue.core import export, settings
from send2ue.dependencies.unreal import UnrealRemoteCalls


class SeparateGroomAssetsExtension(ExtensionBase):
    name = 'separate_groom_assets'

    separate_groom_assets: bpy.props.BoolProperty(
        name="Separate groom assets",
        default=False,
        description=(
            "This individually exports hair particle systems that are surfaced on the same mesh."
        )
    )

    properties = {}

    def pre_operation(self, properties):
        """
        Defines the pre operation logic that stores the scene property group as accessible data for the extension.

        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.separate_groom_assets:
            SeparateGroomAssetsExtension.properties = properties

    def post_groom_export(self, asset_data, properties):
        """
        Defines the post groom export logic that individually exports particle hair systems on a single mesh.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.separate_groom_assets:
            # Gets the asset data of each hair particle system on the current mesh from the head particle system
            assets_data = asset_data['groom_assets_data']
            if len(assets_data) > 1:
                # deselect all particle systems
                self.disable_particles_visibility(assets_data)
                for asset_data in assets_data.values():
                    self.export_individual_hair(asset_data, properties)
                # reselect all particle systems
                self.disable_particles_visibility(assets_data, disable_particles_render=False)

    def post_import(self, asset_data, properties):
        """
        Defines the post import logic that individually imports particle hair systems on a single mesh.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.separate_groom_assets and asset_data.get('groom'):
            property_data = settings.get_extra_property_group_data_as_dictionary(properties, only_key='unreal_type')

            # Gets the asset data of each hair particle system on the current mesh from the head particle system
            assets_data = asset_data['groom_assets_data']
            if len(assets_data) > 1:
                for asset_data in assets_data.values():
                    UnrealRemoteCalls.import_asset(
                        asset_data.get('file_path'),
                        asset_data,
                        property_data
                    )
                    # if create_binding_asset extension is on, create binding asset for each additional groom asset
                    if properties.extensions.create_binding_asset.create_binding_asset:
                        groom_asset_path = asset_data['asset_path']
                        mesh_asset_path = asset_data['mesh_asset_path']
                        UnrealRemoteCalls.create_binding_asset(groom_asset_path, mesh_asset_path)

    def draw_export(self, dialog, layout, properties):
        """
        Draws an interface for the separate_groom_assets option under the export tab.

        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        dialog.draw_property(self, layout, 'separate_groom_assets')

    def export_individual_hair(self, asset_data, properties):
        """
        Exports a particle system with the passed in asset_data as an alembic file.

        :param dict asset_data: A mutable dictionary of asset data for the current particle system.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        # select the particle system to export
        self.disable_particle_visibility(asset_data, disable_particle_render=False)

        # export selection to a file
        file_path = asset_data['file_path']
        # if the folder does not exist create it
        folder_path = os.path.abspath(os.path.join(file_path, os.pardir))
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # export the alembic file
        export.export_alembic_file(file_path, properties)

        # deselect the particle system that exported
        self.disable_particle_visibility(asset_data)

    def disable_particles_visibility(self, assets_data, disable_particles_render=True):
        """
        Toggles the visibility of multiple particle systems referenced by assets_data.

        :param dict assets_data: A mutable dictionary of multiple asset data referencing multiple particle systems.
        :param bool disable_particles_render: Whether to disable or enable particle system visibility.
        """
        for asset_data in assets_data.values():
            self.disable_particle_visibility(asset_data, disable_particles_render)

    @staticmethod
    def disable_particle_visibility(asset_data, disable_particle_render=True):
        """
        Toggles the visibility of a particle systems referenced by asset_data.

        :param dict asset_data: A mutable dictionary of asset data for a particle system referenced by asset_data.
        :param bool disable_particle_render: Whether to disable or enable particle system visibility.
        """
        # dynamically uses what the user has selected in export settings ('RENDER' or 'VIEWPORT') to decide visibility
        show = SeparateGroomAssetsExtension.properties.blender.export_method.abc.scene_options.evaluation_mode

        mesh_object = bpy.data.objects[asset_data['_mesh_object_name']]
        hair_particle = mesh_object.modifiers[asset_data['_modifier_name']]
        setattr(hair_particle, 'show_' + show.lower(), not disable_particle_render)
