# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
import os
from math import degrees
from send2ue.constants import UnrealTypes
from send2ue.core.extension import ExtensionBase
from send2ue.dependencies.unreal import UnrealRemoteCalls
from send2ue.core.utilities import convert_blender_to_unreal_location, get_asset_name

MESH_INSTANCE_NAMES = []


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
            'Instances static meshes in the active level. If the data on an object is linked it will not be '
            're-imported, just instanced. Note that this will force the asset to take on the name of its mesh data, '
            'rather than its object name, and the actors in the unreal level will match the blender object name'
        )
    )

    def pre_operation(self, properties):
        """
        Defines the pre operation logic that stores the scene property group as accessible data for the extension.

        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        MESH_INSTANCE_NAMES.clear()
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
            if asset_type == UnrealTypes.STATIC_MESH:
                mesh_object = bpy.data.objects.get(asset_data['_mesh_object_name'])
                mesh_instance_name = mesh_object.data.name

                # don't export this mesh again
                if mesh_instance_name in MESH_INSTANCE_NAMES:
                    asset_data['skip'] = True

                # rename the asset path to the mesh data name instead of the object name
                asset_path_parts = asset_data['asset_path'].split('/')
                asset_path_parts[-1] = get_asset_name(mesh_object.data.name, properties)
                asset_data['asset_path'] = '/'.join(asset_path_parts)

                # rename the file path to the mesh data name instead of the object name
                file_path = asset_data['file_path']
                _, ext = os.path.splitext(file_path)
                asset_data['file_path'] = os.path.join(
                    os.path.dirname(file_path),
                    f'{mesh_object.data.name}{ext}'
                )

                # track which mesh instances are exported
                MESH_INSTANCE_NAMES.append(mesh_instance_name)

    def post_import(self, asset_data, properties):
        """
        Defines the post import logic that will be an injected operation.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.place_in_active_level:
            scene_object = None
            unique_name = None
            location = [1, 1, 1]
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
                location = scene_object.location
                rotation = [degrees(i) for i in scene_object.rotation_euler]
                scale = scene_object.scale[:]

            # anim sequences use the transforms of the first frame of the action
            if asset_type == UnrealTypes.ANIM_SEQUENCE:
                scene_object = bpy.data.objects.get(asset_data['_armature_object_name'])
                action = bpy.data.actions.get(asset_data['_action_name'])
                unique_name = action.name

                # set the location rotation and scale
                for fcurve in action.fcurves:
                    if fcurve.data_path in ['location', 'scale'] or fcurve.data_path.startswith('rotation'):
                        for keyframe in fcurve.keyframe_points:
                            # only get the value from the start frame
                            if keyframe.co[0] == action.frame_start:
                                if fcurve.data_path == 'location':
                                    location[fcurve.array_index] = keyframe.co[1]
                                elif fcurve.data_path.startswith('rotation'):
                                    rotation[fcurve.array_index] = degrees(keyframe.co[1])
                                elif fcurve.data_path == 'scale':
                                    scale[fcurve.array_index] = keyframe.co[1]
                                break

            if unique_name:
                location = list(scene_object.matrix_world.translation)
                rotation = [degrees(i) for i in scene_object.rotation_euler]
                scale = list(scene_object.scale)

                UnrealRemoteCalls.instance_asset(
                    asset_data['asset_path'],
                    convert_blender_to_unreal_location(location),
                    rotation,
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
