# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
from send2ue.core.extension import ExtensionBase


class ObjectOriginExtension(ExtensionBase):
    name = 'object_origin'
    use_object_origin: bpy.props.BoolProperty(
        name="Use object origin",
        default=False,
        description=(
            "When active, this option will center each object at world origin before it is exported to an FBX, then it "
            "will move each object back to its original position"
        )
    )
    world_center: bpy.props.FloatVectorProperty(default=[0.0, 0.0, 0.0])

    def draw_export(self, dialog, layout, properties):
        """
        Draws an interface for the use_object_origin option under the export tab.

        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        dialog.draw_property(self, layout, 'use_object_origin')

    def pre_mesh_export(self, asset_data, properties):
        """
        Defines the pre mesh export logic that centers object locations.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        # saves original location of asset to asset_data dictionary and sets location to 0
        if self.use_object_origin:
            self.center_object_locations(asset_data['_mesh_object_name'])

    def pre_animation_export(self, asset_data, properties):
        """
        Defines the pre animation export logic that centers actions.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.use_object_origin:
            action = bpy.data.actions.get(asset_data['_action_name'])
            if action:
                action_location = self.set_action_location(action, [0.0, 0.0, 0.0])
                # save action location to dictionary
                self.update_asset_data({
                    '_original_locations': {
                        '_actions': {action.name: action_location}
                    }
                })

    def post_mesh_export(self, asset_data, properties):
        """
        Defines the post mesh export logic the restores the object to their original positions.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.use_object_origin:
            self.restore_object_locations(asset_data)
            self.restore_action_locations(asset_data)

    def post_animation_export(self, asset_data, properties):
        """
        Defines the post animation export logic the restores the actions to their original positions.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        if self.use_object_origin:
            self.restore_action_locations(asset_data)

    def center_object_locations(self, mesh_name):
        """
        Centers a object and its active action to world center.

        :param str mesh_name: The name of the object.
        """
        original_locations = {}
        mesh_object = bpy.data.objects.get(mesh_name)
        if mesh_object:
            original_locations['_objects'] = {}
            # in the case of a skeletal mesh center the armature object
            if mesh_object.parent and mesh_object.parent.type == 'ARMATURE':
                original_locations['_objects'][mesh_object.parent.name] = self.set_object_location(
                    mesh_object.parent,
                    self.world_center
                )
                # center the actions on this armature too so that keyframes don't move
                # the armature back when the scene updates
                original_locations['_actions'] = self.center_action_location(mesh_object.parent)

            # if a static mesh
            else:
                # in the case that the meshes parent is an empty
                if mesh_object.parent and mesh_object.parent.type == 'EMPTY':
                    # center the empty instead of the mesh, thus centering all child meshes
                    original_locations['_objects'][mesh_object.parent.name] = self.set_object_location(
                        mesh_object.parent,
                        self.world_center
                    )
                # otherwise just center the mesh
                else:
                    original_locations['_objects'][mesh_object.name] = self.set_object_location(
                        mesh_object,
                        self.world_center
                    )
        # update the asset data so that it can be accessed in the post export methods
        self.update_asset_data({'_original_locations': original_locations})

    def center_action_location(self, armature_object):
        """
        Centers a armatures active action to world center.

        :param bpy.types.Object armature_object: The name of the object.
        """
        action_locations = {}
        if armature_object.animation_data:
            action = armature_object.animation_data.action
            if action:
                # center the action location keyframes
                action_locations[action.name] = self.set_action_location(action, self.world_center)
        return action_locations

    def restore_object_locations(self, asset_data):
        """
        Restores the original object locations.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        """
        original_locations = asset_data.get('_original_locations', {})
        object_locations = original_locations.get('_objects', {})

        for object_name, object_location in object_locations.items():
            scene_object = bpy.data.objects.get(object_name)
            if scene_object:
                self.set_object_location(scene_object, object_location)

    def restore_action_locations(self, asset_data):
        """
        Restores the original action locations.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        """
        original_locations = asset_data.get('_original_locations', {})
        action_locations = original_locations.get('_actions', {})
        for action_name, action_location in action_locations.items():
            action = bpy.data.actions.get(action_name)
            if action:
                self.set_action_location(action, action_location)

    @staticmethod
    def set_action_location(action, world_location):
        """
        Sets the world location of an action based of the first frame of the action
        and returns its original world location.

        :param bpy.types.Action action: A object.
        :param list world_location: x,y,z coordinates.
        :returns: The original world location values of the given object.
        :rtype: list
        """
        original_location = []
        if action:
            for fcurve in action.fcurves:
                if fcurve.data_path == 'location':
                    # the offset from the first location keyframe and the passed in world location
                    offset = world_location[fcurve.array_index] - fcurve.keyframe_points[0].co[1]
                    for keyframe_point in fcurve.keyframe_points:
                        # save the original location
                        original_location.append(keyframe_point.co[1])

                        # apply the offset to all keys and handles
                        keyframe_point.co[1] = keyframe_point.co[1] + offset
                        keyframe_point.handle_left[1] = keyframe_point.handle_left[1] + offset
                        keyframe_point.handle_right[1] = keyframe_point.handle_right[1] + offset
        return original_location

    @staticmethod
    def set_object_location(scene_object, world_location):
        """
        Sets the world location of the object and returns its original world location.

        :param bpy.types.Object scene_object: A object.
        :param list world_location: x,y,z coordinates.
        :returns: The original world location values of the given object.
        :rtype: list
        """
        original_location = scene_object.location[:]
        scene_object.location = world_location
        return original_location
