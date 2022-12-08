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
    ALL_GROOMS = 'all_grooms'
    CHILD_MESHES_ALL_GROOMS = 'child_meshes_and_all_grooms'


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
            ),
            (
                Options.ALL_GROOMS,
                'All grooms',
                'Combines all hair particle systems and curves objects in the Export collection into a single groom asset',
                '',
                4
            ),
            (
                Options.CHILD_MESHES_ALL_GROOMS,
                'Child meshes and all grooms',
                'For each empty object or armature parent, this combines its child meshes into a single mesh when exported. This also combines all hair particles/objects in the Export collection into a single groom asset',
                '',
                5
            )
        ],
        default=Options.OFF,
        description=(
            "Select how you would like to combine assets in the Export collection."
        )
    )

    combined_groom_name: bpy.props.StringProperty(
        default='Combined_Groom',
        description=(
            'Set a specific name for the groom when using combine "All grooms" or "Child meshes and all grooms"'
        )
    )

    def draw_export(self, dialog, layout, properties):
        """
        Draws an interface for the combine_asset option under the export tab.

        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        row = layout.row()
        property_instance = self.bl_rna.properties.get('combine')
        row.label(text=property_instance.name)
        row.prop(self, 'combine', text='')
        if self.combine in [Options.ALL_GROOMS, Options.CHILD_MESHES_ALL_GROOMS]:
            row.prop(self, 'combined_groom_name', text='')

    def pre_operation(self, properties):
        """
        Defines the pre operation logic that stores the scene property group as accessible data for the extension.

        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        properties.unreal.import_method.fbx.static_mesh_import_data.combine_meshes = False
        # turn on the combine meshes option on the static meshes fbx importer
        if self.combine in [Options.CHILD_MESHES, Options.CHILD_MESHES_ALL_GROOMS, Options.GROOM_PER_COMBINED_MESH]:
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
        if self.combine in [Options.CHILD_MESHES, Options.CHILD_MESHES_ALL_GROOMS, Options.GROOM_PER_COMBINED_MESH]:
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
                    # then only keep this hair object if its unique parents children are also in the list
                    # of filtered meshes from the first condition
                    if all([mesh_object in unique_parent_mesh.parent.children for mesh_object in mesh_objects]):
                        unique_hair_objects.append(hair_object)
                        unique_surface_objects.append(surface_mesh)

            # assign the filtered down hair objects
            hair_objects = unique_hair_objects

        # enum set to combine all grooms
        elif self.combine in [Options.ALL_GROOMS, Options.CHILD_MESHES_ALL_GROOMS]:
            if hair_objects:
                # select one mesh object to be the groom surface object so that export groom runs once
                hair_objects = [hair_objects[0]]

        return armature_objects, mesh_objects, hair_objects

    def pre_mesh_export(self, asset_data, properties):
        """
        Defines the pre mesh export logic that selects all the meshes to be combine and renames them appropriately.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.combine in [Options.CHILD_MESHES, Options.CHILD_MESHES_ALL_GROOMS, Options.GROOM_PER_COMBINED_MESH]:
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
                        'asset_path': f'{asset_folder}{mesh_object.parent.name}'
                    })

    def pre_groom_export(self, asset_data, properties):
        """
        Defines the pre groom export logic that prepares asset data and object selection according to the appropriate
        combine groom option.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        mesh_object = utilities.get_mesh_object_for_groom_name(asset_data.get('_object_name'))
        path, ext = os.path.splitext(asset_data['file_path'])
        asset_folder = asset_data['asset_folder']

        # if combine groom systems for each combined mesh
        if self.combine == Options.GROOM_PER_COMBINED_MESH:
            # get first mesh object under the rig parent to be the name of new surface mesh
            if mesh_object and mesh_object.parent:
                scene_object = None
                if mesh_object.parent.type == 'EMPTY':
                    scene_object = mesh_object.parent
                elif mesh_object.parent.type == 'ARMATURE':
                    child_meshes = utilities.get_meshes_using_armature_modifier(mesh_object.parent)
                    if child_meshes:
                        scene_object = child_meshes[0]

                if scene_object:
                    mesh_asset_name = utilities.get_asset_name(scene_object.name, properties)
                    self.update_asset_data({
                        'file_path': os.path.join(os.path.dirname(path), f'{mesh_asset_name}_{UnrealTypes.GROOM}{ext}'),
                        'asset_path': f'{asset_folder}{mesh_asset_name}_{UnrealTypes.GROOM}'
                    })

        elif self.combine in [Options.ALL_GROOMS, Options.CHILD_MESHES_ALL_GROOMS]:
            # get all mesh objects
            child_mesh_objects = utilities.get_from_collection(BlenderTypes.MESH)
            self.update_asset_data({
                'file_path': os.path.join(os.path.dirname(path), f'{self.combined_groom_name}{ext}'),
                'asset_path': f'{asset_folder}{self.combined_groom_name}'
            })
            # select appropriate child mesh objects to export groom as combined asset
            self.select_for_groom_export(child_mesh_objects)

    @staticmethod
    def select_for_groom_export(mesh_objects):
        """
        Selects multiple mesh objects to prepare for groom export.

        :param list mesh_objects: A list of mesh objects.
        """
        for mesh_object in mesh_objects:
            mesh_object.select_set(True)
            mesh_object.show_instancer_for_render = False
            utilities.set_particles_display_option(mesh_object, False)
            for modifier in utilities.get_particle_system_modifiers(mesh_object):
                utilities.set_particles_display_option(mesh_object, True, only=modifier.particle_system.name)
