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
        if self.separate_groom_assets:
            SeparateGroomAssetsExtension.properties = properties

    def post_groom_export(self, asset_data, properties):
        if self.separate_groom_assets:
            assets_data = asset_data['groom_assets_data']
            if len(assets_data) > 1:
                self.disable_particles_visibility(assets_data)
                for asset_data in assets_data.values():
                    self.export_individual_hair(asset_data, properties)
                self.disable_particles_visibility(assets_data, disable_particles_render=False)

    def post_import(self, asset_data, properties):
        if self.separate_groom_assets and asset_data.get('groom'):
            assets_data = asset_data['groom_assets_data']
            if len(assets_data) > 1:
                for asset_data in assets_data.values():
                    UnrealRemoteCalls.import_asset(asset_data.get('file_path'), asset_data, SeparateGroomAssetsExtension.property_data)

    def draw_export(self, dialog, layout, properties):
        """
        Draws an interface for the separate_groom_assets option under the export tab.

        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        dialog.draw_property(self, layout, 'separate_groom_assets')

    def disable_particles_visibility(self, assets_data, disable_particles_render=True):
        for asset_data in assets_data.values():
            self.disable_particle_visibility(asset_data, disable_particles_render)

    def export_individual_hair(self, asset_data, properties):
        self.disable_particle_visibility(asset_data, disable_particle_render=False)
        # export selection to a file
        file_path = asset_data['file_path']

        # if the folder does not exist create it
        folder_path = os.path.abspath(os.path.join(file_path, os.pardir))
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # export the fbx file
        export.export_alembic_file(file_path, properties)
        self.disable_particle_visibility(asset_data)

    @staticmethod
    def disable_particle_visibility(asset_data, disable_particle_render=True):
        # dynamically uses what the user has selected to
        # TODO: it's really late and this actually appears useless lol
        show = SeparateGroomAssetsExtension.properties.blender.export_method.abc.scene_options.evaluation_mode
        mesh_object = bpy.data.objects[asset_data['_mesh_object_name']]
        setattr(mesh_object.modifiers[asset_data['_hair_particle_name']], show, not disable_particle_render)
        # particle = mesh_object.particle_systems[asset_data['_hair_particle_name']]
