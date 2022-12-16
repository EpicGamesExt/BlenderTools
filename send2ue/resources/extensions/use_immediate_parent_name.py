# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
import os
from send2ue.core.extension import ExtensionBase
from send2ue.core import utilities
from send2ue.constants import ToolInfo, UnrealTypes


class UseImmediateParentNameExtension(ExtensionBase):
    name = 'use_immediate_parent_name'

    use_immediate_parent_name: bpy.props.BoolProperty(
        name="Use immediate parent name",
        default=False,
        description=(
            "This makes the immediate parent the name of the asset"
        )
    )

    def pre_validations(self, properties):
        """
        Defines the pre validations logic that guarantees exclusive usage of some extensions.

        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.use_immediate_parent_name:
            if properties.extensions.use_collections_as_folders.use_collections_as_folders:
                utilities.report_error(
                    f'Cannot use both use collections as folders '
                    f'and use immediate parent name extensions!'
                )
                return False
        return True

    def pre_mesh_export(self, asset_data, properties):
        """
        Defines the pre mesh export logic that modifies export path using immediate parent name as asset name.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.use_immediate_parent_name:
            object_name = asset_data.get('_mesh_object_name', '')
            scene_object = bpy.data.objects[object_name]
            asset_type = utilities.get_mesh_unreal_type(scene_object)
            file_path = self.get_full_file_path(object_name, properties, asset_type)
            self.update_asset_data({
                'file_path': file_path
            })

    def pre_import(self, asset_data, properties):
        """
        Defines the pre import logic that modifies import paths to use immediate parent name as asset name

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.use_immediate_parent_name:
            asset_type = asset_data.get('_asset_type')
            if asset_type and asset_type == UnrealTypes.ANIM_SEQUENCE:
                # if unreal skeleton path has not been set by user
                if not properties.unreal_skeleton_asset_path:
                    object_name = asset_data.get('_armature_object_name', '')
                    rig_object = bpy.data.objects.get(object_name)
                    import_path = self.get_full_import_path(rig_object, properties, UnrealTypes.SKELETAL_MESH)

                    parent_object = rig_object.parent
                    if parent_object and parent_object.type == 'EMPTY':
                        asset_name = parent_object.name
                    else:
                        asset_name = self.get_parent_collection_name(object_name, properties)
                    self.update_asset_data({
                        'skeleton_asset_path': f'{import_path}{asset_name}_Skeleton',
                    })
            elif asset_type:
                object_name = asset_data.get('_mesh_object_name')
                if object_name:
                    mesh_object = bpy.data.objects[object_name]
                    mesh_asset_type = utilities.get_mesh_unreal_type(mesh_object)
                    import_path = self.get_full_import_path(
                        mesh_object,
                        properties,
                        mesh_asset_type
                    )
                    asset_name = self.get_full_asset_name(mesh_object, properties)

                    if asset_type == UnrealTypes.GROOM:
                        # correct the target mesh path for groom asset data
                        self.update_asset_data({
                            'mesh_asset_path': f'{import_path}{asset_name}'
                        })
                    else:
                        self.update_asset_data({
                            'asset_folder': import_path,
                            'asset_path': f'{import_path}{asset_name}',
                        })

    def get_full_asset_name(self, mesh_object, properties):
        """
        Gets the import asset name of the mesh object from its empty type parent object if it exists, if not it will
        get its name from the immediate parent collection.

        :param object mesh_object: A mesh object.
        :param object properties: The property group that contains variables that maintain the addon's correct state.
        :return str: The full asset name when use_immediate_parent_name is active,
        """
        parent_object = mesh_object.parent
        if parent_object:
            # if immediate parent object is of the type empty, return its name as asset name
            if parent_object.type == 'EMPTY':
                return parent_object.name
            # if immediate parent object is of armature type and if grandparent exists
            elif parent_object.type == 'ARMATURE' and parent_object.parent:
                # if grandparent is of the type empty, return its name as asset name
                if parent_object.parent.type == 'EMPTY':
                    return parent_object.parent.name
        # else get asset name from immediate parent collection, return as asset name
        asset_name = self.get_parent_collection_name(mesh_object.name, properties)
        return asset_name

    def get_full_file_path(self, object_name, properties, asset_type, file_extension='fbx'):
        """
        Returns the export path using the immediate parent name as asset name

        :param str object_name: The name of the asset that will be exported to a file.
        :param PropertyData properties: A property data instance that contains all property values of the tool.
        :param str asset_type: The type of data being exported.
        :param str file_extension: The file extension in the file path.
        :return str: The full path to the file.
        """
        export_folder = utilities.get_export_folder_path(properties, asset_type)
        asset_name = self.get_full_asset_name(bpy.data.objects[object_name], properties)

        return os.path.join(
            export_folder,
            f'{asset_name}.{file_extension}'
        )

    def get_full_import_path(self, scene_object, properties, asset_type):
        """
        Gets the unreal import path when using the immediate collection name as the asset name.

        :param object scene_object: A object.
        :param object properties: The property group that contains variables that maintain the addon's correct state.
        :param str asset_type: The type of asset.
        :return str: The import path for the given asset without the immediate parent.
        """
        import_path = utilities.get_import_path(properties, asset_type)
        if import_path:
            parent_object = scene_object.parent
            if not parent_object or parent_object.type != 'EMPTY':
                import_path = self.delete_parent_folder_from_path(scene_object, import_path, properties)

        return import_path

    @staticmethod
    def get_parent_collection_name(asset_name, properties):
        """
        Gets the immediate parent name of the given asset.

        :param str asset_name: The name of the given asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        :return str: The name of the immediate parent of the given asset.
        """
        asset_object = bpy.data.objects.get(asset_name)
        export_collection = bpy.data.collections.get(ToolInfo.EXPORT_COLLECTION.value)

        if asset_object and export_collection:
            parent_collection = utilities.get_parent_collection(asset_object, export_collection)
            if parent_collection and parent_collection.name != ToolInfo.EXPORT_COLLECTION.value:
                return utilities.get_asset_name(parent_collection.name, properties)

    @staticmethod
    def delete_parent_folder_from_path(scene_object, path, properties):
        """
        Removes the given object's immediate parent collection name from the given path.

        :param object scene_object: A object.
        :param str path: A path.
        :param object properties: The property group that contains variables that maintain the addon's correct state.
        :return str: A path where the given object's parent collection is removed.
        """
        export_collection = bpy.data.collections.get(ToolInfo.EXPORT_COLLECTION.value)
        parent_collection = utilities.get_parent_collection(scene_object, export_collection)
        parent_collection_name = utilities.get_asset_name(parent_collection.name, properties)

        path = path.replace(f'{parent_collection_name}/', '')
        return path

    def draw_paths(self, dialog, layout, properties):
        """
        Draws an interface for the use_immediate_collection_name option under the paths tab.

        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        dialog.draw_property(self, layout, 'use_immediate_parent_name')
