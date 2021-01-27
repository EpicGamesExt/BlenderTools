# Copyright Epic Games, Inc. All Rights Reserved.
import os
import bpy
import unittest
import unreal_utilities


class Send2UeUseObjectOriginTestCases(unittest.TestCase):
    """
    related issue:
    https://github.com/EpicGames/BlenderTools/issues/223
    This test ensure that the 'use_object_origin' option is working correctly.
    """

    def setUp(self):
        # load in the file you will run tests on
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'static_meshes.blend'))

        # enable the required addons
        bpy.ops.preferences.addon_enable(module='send2ue')

        # Make sure the import area is clean
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')

    def tearDown(self):
        # restore blend file to the default test file
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'default_startup.blend'))

    def test_use_object_origin_true(self):
        """
        This method turns on 'use_object_origin' and sends a mesh to unreal, then check that the position was restored.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences
        cube = bpy.data.objects['Cube']

        # move the cube to the mesh collection
        bpy.data.collections['Mesh'].objects.link(cube)
        bpy.context.scene.collection.objects.unlink(cube)

        # turn on the use object origin option
        properties.use_object_origin = True

        # set the cube to (1, 1, 1) in world space
        cube.location.x = 1
        cube.location.y = 1
        cube.location.z = 1

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the cube was return to its original position
        self.assertTrue(cube.location.x == 1)
        self.assertTrue(cube.location.y == 1)
        self.assertTrue(cube.location.z == 1)

        # delete all the assets created by the import
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')

        # turn on the use object origin option
        properties.use_object_origin = False

        # move the cube out of the mesh collection
        bpy.context.scene.collection.objects.link(cube)
        bpy.data.collections['Mesh'].objects.unlink(cube)
