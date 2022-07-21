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

    def draw_export(self, dialog, layout, properties):
        row = layout.row()
        row.prop(self, 'use_object_origin')

    # saves original location of asset to asset_data dictionary, set location to 0
    def pre_mesh_export(self, asset_data, properties):
        if self.use_object_origin:
            asset_data['_original_position'] = self.set_object_location(
                asset_data['_mesh_object_name'],
                [0, 0, 0]
            )

    # restores original location of asset
    def post_mesh_export(self, asset_data, properties):
        if self.use_object_origin:
            self.set_object_location(
                asset_data['_mesh_object_name'],
                asset_data['_original_position']
            )

    def set_object_location(self, name, location):
        """
        This function gets the original world position and centers the object at world zero for export.

        :param str name: Name of object to relocate.
        :param list location: x,y,z coordinates.
        :returns: A tuple that is the original position values of the selected object.
        :rtype: list
        """
        scene_object = bpy.data.objects.get(name)
        if scene_object:
            original_position = scene_object.location[:]
            scene_object.location = location
            return original_position
