# Copyright Epic Games, Inc. All Rights Reserved.

import os
import bpy
from send2ue.core.extension import ExtensionBase
from send2ue.core import export, settings, utilities
from send2ue.dependencies.unreal import UnrealRemoteCalls
from send2ue.constants import AssetTypes


class CombineGroomExtension(ExtensionBase):
    name = 'combine_groom_assets'

    properties = {}
    combine_groom_combine_mesh = False

    combine_groom_assets: bpy.props.EnumProperty(
        name="Combine grooms",
        items=[
            (
                'off',
                'Off',
                'Each hair particle system and curves object will export individually',
                '',
                0
            ),
            (
                'combine_groom_for_each_mesh',
                'Combine groom for each mesh',
                'Combine hair surfaced on the same mesh as a groom asset for each mesh in the Export collection',
                '',
                1
            ),
            (
                'combine_all_groom',
                'Combine all groom',
                'Combine all hair particle systems and curves objects in the Export collection into one groom asset',
                '',
                2
            )
        ],
        default='off',
        description=(
            "Select how you would like to combine hair particle systems and curves objects into groom assets."
        )
    )

    def draw_export(self, dialog, layout, properties):
        """
        Draws an interface for the combine_groom_asset option under the export tab.

        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        dialog.draw_property(self, layout, 'combine_groom_assets')

    def pre_operation(self, properties):
        """
        Defines the pre operation logic that stores the scene property group as accessible data for the extension.

        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        # stores the scene property group as accessible data for the extension
        CombineGroomExtension.properties = properties

        # stores the boolean condition where both combine meshes and combine groom for each mesh are used
        combine_for_each_mesh = self.combine_groom_assets == CombineOptions.COMBINE_FOR_EACH_MESH
        combine_meshes = properties.extensions.combine_meshes.combine_child_meshes
        CombineGroomExtension.combine_groom_combine_mesh = combine_for_each_mesh and combine_meshes

    def filter_objects(self, armature_objects, mesh_objects):
        """
        Filters armature and mesh objects for the appropriate combine groom option.

        :param list[object] armature_objects: A list of armature objects.
        :param list[object] mesh_objects: A list of mesh objects.
        :returns: A tuple which contains filtered lists of armature objects, mesh objects and groom surface objects.
        :rtype: tuple(list, list, list)
        """
        groom_surface_objects = mesh_objects

        # combine meshes extension is on and enum set to combine for each groom
        if CombineGroomExtension.combine_groom_combine_mesh:
            # groom surface objects are meshes with unique parents
            groom_surface_objects = utilities.get_unique_parent_mesh_objects(armature_objects, mesh_objects)

        # enum set to combine all groom
        elif self.combine_groom_assets == CombineOptions.COMBINE_ALL:
            if len(mesh_objects) > 0:
                # select one mesh object to be the groom surface object so that export groom runs once
                groom_surface_objects = [mesh_objects[0]]

        return armature_objects, mesh_objects, groom_surface_objects

    def pre_groom_export(self, asset_data, properties):
        """
        Defines the pre groom export logic that prepares asset data and object selection according to the appropriate
        combine groom option.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        # if combine groom systems for each combined mesh
        if CombineGroomExtension.combine_groom_combine_mesh:
            mesh_object_name = asset_data.get('_mesh_object_name')
            mesh_object = bpy.data.objects.get(mesh_object_name)
            if mesh_object and mesh_object.parent:
                # get the child hierarchy of the mesh parent excluding socket, collision, etc.
                child_mesh_objects = utilities.get_all_children(
                    mesh_object.parent,
                    AssetTypes.MESH,
                    properties,
                    exclude_postfix_tokens=True
                )

                if self.hair_particles_exist(child_mesh_objects + [mesh_object]):
                    groom_asset_name = mesh_object_name + '_groom'
                    # update and populate asset data if asset data is empty (when the head mesh has no particle systems)
                    self.update_asset_data(
                        export.create_groom_system_data(properties, groom_asset_name, mesh_object_name)
                    )
                    # select appropriate child mesh objects to export groom as combined asset
                    self.select_for_groom_export(child_mesh_objects)

        elif self.combine_groom_assets == CombineOptions.OFF:
            if properties.extensions.combine_meshes.combine_child_meshes:
                # original surface mesh
                surface_object_name = asset_data.get('_mesh_object_name')
                surface_object = bpy.data.objects.get(surface_object_name)

                # get first mesh object under the rig parent to be the name of new surface mesh
                if surface_object and surface_object.parent:
                    mesh_object = utilities.get_rig_child_meshes(surface_object.parent, index=0)
                    if mesh_object:
                        mesh_import_path = utilities.get_import_path(properties, AssetTypes.MESH)
                        mesh_asset_name = utilities.get_asset_name(mesh_object.name, properties)

                        # update surface mesh so binding asset factory can find appropriate target skeletal mesh
                        self.update_asset_data({
                            '_mesh_object_name': mesh_object.name,
                            'mesh_asset_path': f'{mesh_import_path}{mesh_asset_name}'
                        })

        elif self.combine_groom_assets == CombineOptions.COMBINE_ALL:
            groom_asset_name = 'combined_groom'
            # get all mesh objects
            child_mesh_objects = utilities.get_from_collection(AssetTypes.MESH, properties)
            if self.hair_particles_exist(child_mesh_objects):
                # only updates asset name since no binding asset will be created
                self.update_asset_data(
                    export.create_groom_system_data(properties, groom_asset_name)
                )
                # delete mesh object related attributes so binding asset won't be created for the combine all groom
                self.del_asset_data_items(['_mesh_object_name', 'mesh_asset_path'])

                # select appropriate child mesh objects to export groom as combined asset
                self.select_for_groom_export(child_mesh_objects)

    def post_groom_export(self, asset_data, properties):
        """
        Defines the post groom export logic for the appropriate combine groom option.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        # if export each system individually, get and export all systems on the current mesh individually
        if self.combine_groom_assets == CombineOptions.OFF:
            # Gets the asset data of each hair particle system on the current mesh from the head particle system
            groom_systems_data = asset_data.get('groom_systems_data')
            if groom_systems_data and len(groom_systems_data) > 1:
                self.export_individual_hair_systems(groom_systems_data.values(), properties)

        # remove particle systems converted from curves for options that don't get to iterate through every mesh
        curves_object_names = asset_data['converted_curves']
        mesh_objects = []

        if CombineGroomExtension.combine_groom_combine_mesh:
            mesh_object_name = asset_data.get('_mesh_object_name')
            mesh_object = bpy.data.objects.get(mesh_object_name)
            mesh_objects = utilities.get_all_children(
                mesh_object.parent,
                AssetTypes.MESH,
                properties,
                exclude_postfix_tokens=True
            )
        if self.combine_groom_assets == CombineOptions.COMBINE_ALL:
            mesh_objects = utilities.get_from_collection(AssetTypes.MESH, properties)

        # remove particle systems that were converted from curves on associated mesh objects of the current mesh
        utilities.remove_particle_systems(curves_object_names, mesh_objects)

    def post_import(self, asset_data, properties):
        """
        Defines the post import logic for the appropriate combine groom option.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.combine_groom_assets == CombineOptions.OFF and asset_data.get('groom'):
            property_data = settings.get_extra_property_group_data_as_dictionary(properties, only_key='unreal_type')

            # Gets the asset data of each hair particle system on the current mesh from the head particle system
            systems_data = asset_data['groom_systems_data']
            if len(systems_data) > 1:
                for system_data in systems_data.values():
                    # import individual particle systems on the current mesh
                    UnrealRemoteCalls.import_asset(
                        system_data.get('file_path'),
                        system_data,
                        property_data
                    )
                    # if create_binding_asset extension is on, create binding asset for each additional groom asset
                    if properties.extensions.create_binding_asset.create_binding_asset:
                        groom_asset_path = system_data['asset_path']
                        # use mesh_asset_path from asset_data instead of system_data because pre-export could update it
                        mesh_asset_path = asset_data['mesh_asset_path']
                        UnrealRemoteCalls.create_binding_asset(groom_asset_path, mesh_asset_path)

    def export_individual_hair_systems(self, assets_data, properties):
        """
        Exports particle systems associated with assets_data as alembic files.

        :param list assets_data: A list of mutable dictionary of asset data for particle systems.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        # deselect all particle systems
        self.disable_particles_visibility(assets_data)

        for asset_data in assets_data:
            # select the particle system to export
            self.disable_particles_visibility([asset_data], disable_particles_render=False)

            # export selection to a file
            file_path = asset_data['file_path']
            # if the folder does not exist create it
            folder_path = os.path.abspath(os.path.join(file_path, os.pardir))
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            # export the alembic file
            export.export_alembic_file(file_path, properties)

            # deselect the particle system that exported
            self.disable_particles_visibility([asset_data])

        # reselect all particle systems
        self.disable_particles_visibility(assets_data, disable_particles_render=False)

    @staticmethod
    def select_for_groom_export(mesh_objects):
        """
        Selects multiple mesh objects to prepare for groom export.

        :param list mesh_objects: A list of mesh objects.
        """
        utilities.deselect_all_objects()
        for mesh_object in mesh_objects:
            if len(mesh_object.particle_systems) > 0:
                mesh_object.select_set(True)
                # turn show_emitter off in particle system render settings
                mesh_object.show_instancer_for_render = False

    @staticmethod
    def hair_particles_exist(mesh_objects):
        """
        Determines if hair particle systems exist on a list of meshes.

        :param list mesh_objects: A list of mesh objects.
        :return bool: Whether any hair particle systems exist on list of meshes.
        """
        for mesh_object in mesh_objects:
            hair_particles = utilities.get_particle_systems(mesh_object, 'HAIR')
            if len(hair_particles) > 0:
                return True
        return False

    @staticmethod
    def disable_particles_visibility(assets_data, disable_particles_render=True):
        """
        Toggles the visibility of multiple particle systems referenced by assets_data.

        :param list assets_data: A list of mutable dictionary of asset data for particle systems.
        :param bool disable_particles_render: Whether to disable or enable particle system visibility.
        """
        # dynamically uses what the user selected in export settings ('RENDER' or 'VIEWPORT') to decide visibility
        show = CombineGroomExtension.properties.blender.export_method.abc.scene_options.evaluation_mode

        for asset_data in assets_data:
            mesh_object = bpy.data.objects[asset_data['_mesh_object_name']]
            hair_particle = mesh_object.modifiers[asset_data['_modifier_name']]
            setattr(hair_particle, 'show_' + show.lower(), not disable_particles_render)


class CombineOptions:
    OFF = 'off'
    COMBINE_FOR_EACH_MESH = 'combine_groom_for_each_mesh'
    COMBINE_ALL = 'combine_all_groom'
