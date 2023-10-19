# Copyright Epic Games, Inc. All Rights Reserved.

import os
import bpy
from send2ue.core.extension import ExtensionBase
from send2ue.core import utilities
from send2ue.constants import BlenderTypes, UnrealTypes


class Options:
    OFF = 'off'
    CHILD_MESHES = 'child_meshes'
    GROOM_PER_MESH = 'groom_per_mesh'
    GROOM_PER_COMBINED_MESH = 'groom_per_combined_mesh'


class CombineAssetsExtension(ExtensionBase):
    name = 'combine_assets'

    combine: bpy.props.EnumProperty(
        name="Combine assets",
        items=[
            (
                Options.OFF,
                'Off',
                'All objects and systems in the Export collection export as individual assets',
                '',
                0
            ),
            (
                Options.CHILD_MESHES,
                'Child meshes',
                'For each empty object or armature parent, this combines its child meshes into a single mesh when exported',
                '',
                1
            ),
            (
                Options.GROOM_PER_MESH,
                'Groom for each mesh',
                'For each mesh in the Export collection, this combines every hair objects/systems surfaced on the mesh as a single groom asset',
                '',
                2
            ),
            (
                Options.GROOM_PER_COMBINED_MESH,
                'Groom for each combined mesh',
                'For each empty object or armature parent, this combines its child meshes into a single mesh when exported. For each combined mesh, all hair objects/systems surfaced on it are exported as a single groom asset',
                '',
                3
            )
        ],
        default=Options.OFF,
        description=(
            "Select how you would like to combine assets in the Export collection."
        )
    )

    def draw_export(self, dialog, layout, properties):
        """
        Draws an interface for the combine_asset option under the export tab.

        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        box = layout.box()
        dialog.draw_property(self, box, 'combine')

    def pre_operation(self, properties):
        """
        Defines the pre operation logic that stores the scene property group as accessible data for the extension.

        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        properties.unreal.import_method.fbx.static_mesh_import_data.combine_meshes = False
        # turn on the combine meshes option on the static meshes fbx importer
        if self.combine in [Options.CHILD_MESHES, Options.GROOM_PER_COMBINED_MESH]:
            properties.unreal.import_method.fbx.static_mesh_import_data.combine_meshes = True

    def filter_objects(self, armature_objects, mesh_objects, hair_objects):
        """
        Filters armature and mesh objects for the appropriate combine groom option.

        :param list[object] armature_objects: A list of armature objects.
        :param list[object] mesh_objects: A list of mesh objects.
        :param list[object] hair_objects: A list of hair objects.
        :returns: A tuple which contains filtered lists of armature objects, mesh objects and groom surface objects.
        :rtype: tuple(list, list, list)
        """
        if self.combine in [Options.CHILD_MESHES, Options.GROOM_PER_COMBINED_MESH]:
            mesh_objects = utilities.get_unique_parent_mesh_objects(armature_objects, mesh_objects)

        if self.combine == Options.GROOM_PER_COMBINED_MESH:
            unique_surface_objects = []
            unique_hair_objects = []
            for hair_object in hair_objects:
                # get the surface mesh related to the hair object
                surface_mesh = utilities.get_mesh_object_for_groom_name(hair_object.name)
                # don't check this if it has already been checked
                if surface_mesh in unique_surface_objects:
                    continue
                # get the unique parent meshes related to that surface mesh
                unique_parent_meshes = utilities.get_unique_parent_mesh_objects(armature_objects, [surface_mesh])
                for unique_parent_mesh in unique_parent_meshes:
                    # then only keep this hair object if any of its unique parents children are also in the list
                    # of filtered meshes from the first condition
                    if any([mesh_object in mesh_objects for mesh_object in unique_parent_mesh.parent.children]):
                        unique_hair_objects.append(hair_object)
                        unique_surface_objects.append(surface_mesh)

            # assign the filtered down hair objects
            hair_objects = unique_hair_objects

        elif self.combine == Options.GROOM_PER_MESH:
            unique_surface_objects = []
            unique_hair_objects = []
            for hair_object in hair_objects:
                # get the surface mesh related to the hair object
                surface_mesh = utilities.get_mesh_object_for_groom_name(hair_object.name)
                # make sure only one hair object is related to one mesh
                if surface_mesh in unique_surface_objects:
                    continue
                if surface_mesh in mesh_objects:
                    unique_hair_objects.append(hair_object)
                    unique_surface_objects.append(surface_mesh)
            # assign the filtered down hair objects
            hair_objects = unique_hair_objects

        return armature_objects, mesh_objects, hair_objects

    def pre_mesh_export(self, asset_data, properties):
        """
        Defines the pre mesh export logic that selects all the meshes to be combine and renames them appropriately.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.combine in [Options.CHILD_MESHES, Options.GROOM_PER_COMBINED_MESH]:
            mesh_object_name = asset_data.get('_mesh_object_name', '')
            mesh_object = bpy.data.objects.get(mesh_object_name)
            if mesh_object and mesh_object.parent:
                # select the child hierarchy of the mesh parent excluding socket, collision, etc.
                utilities.select_all_children(
                    mesh_object.parent,
                    BlenderTypes.MESH,
                    exclude_postfix_tokens=True
                )
                # rename the asset to match the empty if this is a static mesh export
                if mesh_object.parent.type == 'EMPTY':
                    path, ext = os.path.splitext(asset_data['file_path'])
                    asset_folder = asset_data['asset_folder']

                    # select the corresponding collisions for each selected child mesh
                    for selected_mesh in bpy.context.selected_objects:
                        utilities.select_asset_collisions(selected_mesh.name, properties)

                    self.update_asset_data({
                        'file_path': os.path.join(os.path.dirname(path), f'{mesh_object.parent.name}{ext}'),
                        'asset_path': f'{asset_folder}{mesh_object.parent.name}',
                        'empty_object_name': mesh_object.parent.name
                    })

    def pre_groom_export(self, asset_data, properties):
        """
        Defines the pre groom export logic that prepares asset data and object selection according to the appropriate
        combine groom option.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        path, ext = os.path.splitext(asset_data['file_path'])
        asset_folder = asset_data['asset_folder']

        if self.combine in [Options.GROOM_PER_MESH, Options.GROOM_PER_COMBINED_MESH]:
            # get the mesh asset data related to this groom asset data
            mesh_asset_data = utilities.get_related_mesh_asset_data_from_groom_asset_data(asset_data)
            mesh_asset_name = mesh_asset_data.get('asset_path', '').split('/')[-1]
            mesh_object = bpy.data.objects.get(mesh_asset_data.get('_mesh_object_name', ''))
            if mesh_asset_name:
                self.update_asset_data({
                    'file_path': os.path.join(os.path.dirname(path), f'{mesh_asset_name}_{UnrealTypes.GROOM}{ext}'),
                    'asset_path': f'{asset_folder}{mesh_asset_name}_{UnrealTypes.GROOM}'
                })
            if mesh_object:
                if self.combine == Options.GROOM_PER_MESH:
                    self.select_for_groom_export([mesh_object], properties)

                elif self.combine == Options.GROOM_PER_COMBINED_MESH:
                    rig_object = utilities.get_armature_modifier_rig_object(mesh_object)
                    unique_parent_meshes = utilities.get_unique_parent_mesh_objects([rig_object], [mesh_object])
                    if len(unique_parent_meshes) == 1 and unique_parent_meshes[0].parent:
                        mesh_objects = [
                            scene_object for scene_object in unique_parent_meshes[0].parent.children if
                            scene_object.type == BlenderTypes.MESH
                        ]
                        # select all child objects under the unique parent
                        self.select_for_groom_export(mesh_objects, properties)

    @staticmethod
    def select_for_groom_export(mesh_objects, properties):
        """
        Selects multiple mesh objects to prepare for groom export.

        :param list mesh_objects: A list of mesh objects.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        related_mesh_objects = []

        # hide all particle systems on the mesh objects
        for mesh_object in mesh_objects:
            utilities.set_particles_display_option(mesh_object, False)

        for hair_object in utilities.get_hair_objects(properties):
            # if this is a curves object convert it to a particle system
            if type(hair_object) == bpy.types.Object:
                utilities.convert_curve_to_particle_system(hair_object)
            mesh_object = utilities.get_mesh_object_for_groom_name(hair_object.name)
            # add the hair particle system to the export
            utilities.set_particles_display_option(mesh_object, True, only=hair_object.name)

            if mesh_object in mesh_objects:
                related_mesh_objects.append(mesh_object)

        # deselect everything
        utilities.deselect_all_objects()

        # select all the meshes to export
        for related_mesh_object in related_mesh_objects:
            related_mesh_object.select_set(True)
            related_mesh_object.show_instancer_for_render = False
