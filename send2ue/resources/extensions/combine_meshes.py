# Copyright Epic Games, Inc. All Rights Reserved.

import os
import bpy
from send2ue.core.extension import ExtensionBase
from send2ue.core import utilities
from send2ue.constants import AssetTypes


class CombineMeshesExtension(ExtensionBase):
    name = 'combine_meshes'

    combine_child_meshes: bpy.props.BoolProperty(
        name="Combine child meshes",
        default=False,
        description=(
            "This combines all child meshes of an empty object or armature object into a single mesh when exported"
        )
    )

    def filter_objects(self, armature_objects, mesh_objects):
        """
        Defines a filter for the armature and mesh objects so that only unique parent meshes are collected.

        :param list[object] armature_objects: A list of armature objects.
        :param list[object] mesh_objects: A list of mesh objects.
        :returns: A tuple which contains filtered lists of armature objects, mesh objects and groom surface objects.
        :rtype: tuple(list, list, list)
        """
        groom_surface_objects = mesh_objects
        if self.combine_child_meshes:
            mesh_objects = utilities.get_unique_parent_mesh_objects(armature_objects, mesh_objects)
        return armature_objects, mesh_objects, groom_surface_objects

    def pre_operation(self, properties):
        """
        Defines the pre operation logic that forces the unreal static mesh import setting to combine meshes on import.

        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        properties.unreal.import_method.fbx.static_mesh_import_data.combine_meshes = False
        # turn on the combine meshes option on the static meshes fbx importer
        if self.combine_child_meshes:
            properties.unreal.import_method.fbx.static_mesh_import_data.combine_meshes = True

    def draw_export(self, dialog, layout, properties):
        """
        Draws an interface for the combine_child_meshes option under the export tab.

        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        dialog.draw_property(self, layout, 'combine_child_meshes')

    def pre_mesh_export(self, asset_data, properties):
        """
        Defines the pre mesh export logic that selects all the meshes to be combine and renames them appropriately.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.combine_child_meshes:
            mesh_object_name = asset_data.get('_mesh_object_name', '')
            mesh_object = bpy.data.objects.get(mesh_object_name)
            if mesh_object and mesh_object.parent:
                # select the child hierarchy of the mesh parent excluding socket, collision, etc.
                utilities.select_all_children(
                    mesh_object.parent,
                    AssetTypes.MESH,
                    properties,
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
