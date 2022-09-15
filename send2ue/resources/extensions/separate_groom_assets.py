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

    def post_groom_export(self, asset_data, properties):
        if self.separate_groom_assets:
            assets_data = asset_data['groom_assets_data']
            if len(assets_data) > 1:
                self.change_particles_type(assets_data, 'EMITTER')
                for asset_data in assets_data.values():
                    self.export_individual_hair(asset_data, properties)
                self.change_particles_type(assets_data, 'HAIR')

    def pre_import(self, asset_data, properties):
        property_data = settings.get_extra_property_group_data_as_dictionary(properties, only_key='unreal_type')
        if self.separate_groom_assets and asset_data.get('groom'):
            assets_data = asset_data['groom_assets_data']
            if len(assets_data) > 1:
                for asset_data in assets_data.values():
                    UnrealRemoteCalls.import_asset(asset_data.get('file_path'), asset_data, property_data)

    def draw_export(self, dialog, layout, properties):
        """
        Draws an interface for the separate_groom_assets option under the export tab.

        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        dialog.draw_property(self, layout, 'separate_groom_assets')

    def change_particles_type(self, assets_data, particle_type):
        for asset_data in assets_data.values():
            self.change_particle_type(asset_data, particle_type)

    def export_individual_hair(self, asset_data, properties):
        self.change_particle_type(asset_data, 'HAIR')
        # export selection to a file
        file_path = asset_data['file_path']

        # if the folder does not exist create it
        folder_path = os.path.abspath(os.path.join(file_path, os.pardir))
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # export the fbx file
        export.export_alembic_file(file_path, properties)
        self.change_particle_type(asset_data, 'EMITTER')

    @staticmethod
    def change_particle_type(asset_data, particle_type):
        mesh_object = bpy.data.objects[asset_data['_mesh_object_name']]
        particle = mesh_object.particle_systems[asset_data['_hair_particle_name']]
        particle.settings.type = particle_type
