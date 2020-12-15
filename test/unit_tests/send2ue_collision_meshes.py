# Copyright Epic Games, Inc. All Rights Reserved.
import os
import bpy
import unittest
import unreal_utilities


class Send2UeCollisionsTestCases(unittest.TestCase):
    """
    related issue:
    https://github.com/EpicGames/BlenderTools/issues/22
    """

    def setUp(self):
        # load in the file you will run tests on
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'collision_meshes.blend'))

        # enable the required addons
        bpy.ops.preferences.addon_enable(module='send2ue')

    def tearDown(self):
        # restore blend file to the default test file
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'default_startup.blend'))

    def test_send_collision_meshes_to_unreal(self):
        """
        This method sends several different collision meshes and checks that those collision meshes exist in Unreal.
        """
        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the collision meshes exist in the unreal project
        self.assertTrue(unreal_utilities.has_custom_collision('/Game/untitled_category/untitled_asset/SM_Capsule'))
        self.assertTrue(unreal_utilities.has_custom_collision('/Game/untitled_category/untitled_asset/SM_CubeConvex'))
        self.assertTrue(unreal_utilities.has_custom_collision('/Game/untitled_category/untitled_asset/SM_CubeNoSuffix'))
        self.assertTrue(unreal_utilities.has_custom_collision('/Game/untitled_category/untitled_asset/SM_Sphere'))

        # This object actually has several collision meshes but unreal.StaticMesh can't count them.
        self.assertTrue(unreal_utilities.has_custom_collision('/Game/untitled_category/untitled_asset/SM_CubeSuffix'))

        # delete all the assets created by the import
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')

    def test_send_without_collision_meshes(self):
        """
        This method sends a mesh without any collision meshes and verifies that it isn't included in Unreal.
        """
        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check that objects without a collision mesh doesn't have one in the unreal project
        self.assertFalse(unreal_utilities.has_custom_collision('/Game/untitled_category/untitled_asset/SM_CubeNoCollisionMesh'))

        # delete all the assets created by the import
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')
