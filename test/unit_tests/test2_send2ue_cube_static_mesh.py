# Copyright Epic Games, Inc. All Rights Reserved.
import os
import bpy
import unittest
import unreal_utilities


# TODO add github feature issue link
class Send2UeCubeStaticMeshTestCases(unittest.TestCase):

    def setUp(self):
        """
        This method is called before any of the methods in this unit test are run.
        """
        # load in the file you will run tests on
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'cube_static_mesh.blend'))

    def test_send_cube_to_unreal(self):
        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the cube exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/Cube'))

        # delete the cube
        unreal_utilities.delete_asset('/Game/untitled_category/untitled_asset/Cube')

    def tearDown(self):
        """
        This method is called after all of the methods in this unit test are run.
        """
        # restore blend file to the default test file
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'default_startup.blend'))