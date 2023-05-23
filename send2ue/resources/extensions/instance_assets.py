# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
import os
from send2ue.constants import UnrealTypes
from send2ue.core.extension import ExtensionBase
from send2ue.dependencies.unreal import UnrealRemoteCalls
from send2ue.core.utilities import (
    convert_blender_rotation_to_unreal_rotation,
    convert_blender_to_unreal_location,
    get_armature_modifier_rig_object,
    get_asset_name
)

STATIC_MESH_INSTANCE_NAMES = []
SKELETAL_MESH_INSTANCE_NAMES = []


class InstanceAssetsExtension(ExtensionBase):
    name = 'instance_assets'

    # ------------ read/write ---------------
    use_object_origin_state: bpy.props.BoolProperty(default=False)

    # ------------ ui -----------------------
    place_in_active_level: bpy.props.BoolProperty(
        default=False,
        name='Place in active level',
        description='Spawns assets in the active level at the same location they are positioned in the blender scene'
    )
    use_mesh_instances: bpy.props.BoolProperty(
        default=False,
        name='Use mesh instances',
        description=(
            'Instances static and skeletal meshes in the active level. If the data on an object is linked it will not '
            'be re-imported, just instanced. Note that this will force the asset to take on the name of its mesh data, '
            'rather than its object name, and the actors in the unreal level will match the blender object name'
        )
    )

    @staticmethod
    def _rename_asset(asset_data, name, properties):
        """
        Renames the asset data with the given name.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param str name: The new name of the asset.
        """
        asset_name = get_asset_name(name, properties)

        # rename the asset path to the mesh data name instead of the object name
        asset_path_parts = asset_data['asset_path'].split('/')
        asset_path_parts[-1] = asset_name
        asset_data['asset_path'] = '/'.join(asset_path_parts)

        # rename the file path to the mesh data name instead of the object name
        file_path = asset_data['file_path']
        _, ext = os.path.splitext(file_path)
        asset_data['file_path'] = os.path.join(
            os.path.dirname(file_path),
            f'{asset_name}{ext}'
        )

    def pre_operation(self, properties):
        """
        Defines the pre operation logic that stores the scene property group as accessible data for the extension.

        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        STATIC_MESH_INSTANCE_NAMES.clear()
        SKELETAL_MESH_INSTANCE_NAMES.clear()
        if self.place_in_active_level:
            self.use_object_origin_state = properties.use_object_origin
            properties.use_object_origin = True

    def post_operation(self, properties):
        """
        Defines the post operation logic that will be run after the send to unreal operation.

        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.place_in_active_level:
            properties.use_object_origin = self.use_object_origin_state

    def pre_mesh_export(self, asset_data, properties):
        """
        Defines the pre mesh export logic that will be an injected operation.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.use_mesh_instances:
            asset_type = asset_data['_asset_type']
            mesh_object = bpy.data.objects.get(asset_data['_mesh_object_name'])
            mesh_instance_name = mesh_object.data.name

            if asset_type == UnrealTypes.STATIC_MESH:
                # don't export this static mesh again
                if mesh_instance_name in STATIC_MESH_INSTANCE_NAMES:
                    asset_data['skip'] = True

                self._rename_asset(asset_data, mesh_instance_name, properties)
                # track which static mesh instances are exported
                STATIC_MESH_INSTANCE_NAMES.append(mesh_instance_name)

            if asset_type == UnrealTypes.SKELETAL_MESH:
                rig_object = get_armature_modifier_rig_object(mesh_object) or mesh_object.parent

                # don't export this skeletal mesh again
                if (mesh_instance_name, rig_object.data.name) in SKELETAL_MESH_INSTANCE_NAMES:
                    asset_data['skip'] = True

                self._rename_asset(asset_data, mesh_instance_name, properties)
                # track which skeletal mesh instances are exported
                SKELETAL_MESH_INSTANCE_NAMES.append((mesh_instance_name, rig_object.data.name))

    def post_import(self, asset_data, properties):
        """
        Defines the post import logic that will be an injected operation.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.place_in_active_level:
            unique_name = None
            location = [0, 0, 0]
            rotation = [0, 0, 0]
            scale = [1, 1, 1]

            asset_type = asset_data['_asset_type']

            # static and skeletal meshes use the mesh objects transforms
            if asset_type in [
                UnrealTypes.STATIC_MESH,
                UnrealTypes.SKELETAL_MESH
            ]:
                scene_object = bpy.data.objects.get(asset_data['_mesh_object_name'])
                unique_name = scene_object.name
                location = list(scene_object.matrix_world.translation)
                rotation = scene_object.rotation_euler
                scale = scene_object.scale[:]

            # anim sequences use the transforms of the first frame of the action
            if asset_type == UnrealTypes.ANIM_SEQUENCE:
                # the transforms default to the armature object location
                scene_object = bpy.data.objects.get(asset_data['_armature_object_name'])
                location = list(scene_object.matrix_world.translation)
                rotation = scene_object.rotation_euler
                scale = scene_object.scale[:]

                action = bpy.data.actions.get(asset_data['_action_name'])
                unique_name = action.name

                # otherwise the if location is in the action curves, that first frame determines
                # the actors location in the level
                for fcurve in action.fcurves:
                    for keyframe in fcurve.keyframe_points:
                        if fcurve.data_path == 'location':
                            # only get the value from the start frame
                            if keyframe.co[0] == action.frame_range[0]:
                                location[fcurve.array_index] = keyframe.co[1]
                            break

            if unique_name:
                UnrealRemoteCalls.instance_asset(
                    asset_data['asset_path'],
                    convert_blender_to_unreal_location(location),
                    convert_blender_rotation_to_unreal_rotation(rotation),
                    scale,
                    unique_name
                )

    def draw_import(self, dialog, layout, properties):
        """
        Defines the draw method for the extension under the `Export` tab.
        """
        box = layout.box()
        box.label(text='Instance Assets:')
        row = box.row()
        dialog.draw_property(self, row, 'place_in_active_level')
        row = box.row()
        if not self.place_in_active_level:
            row.enabled = False
        dialog.draw_property(self, row, 'use_mesh_instances')
