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
        """
        This method is called before any of the methods in this unit test are run.
        """
        # load in the file you will run tests on
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'collision_meshes.blend'))

        # enable the required addons
        bpy.ops.preferences.addon_enable(module='send2ue')

    def test_send_collision_meshes_to_unreal(self):
        """
        This method sends 
        """
        capsule_collision = bpy.data.objects['SM_Capsule']
        cubeConvex_collision = bpy.data.objects['SM_CubeConvex']
        cubeSuffix_collision = bpy.data.objects['SM_CubeSuffix']
        cubeNoSuffix_collision = bpy.data.objects['SM_CubeNoSuffix']
        sphere_collision = bpy.data.objects['SM_Sphere']


        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the collision meshes exist in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SM_Capsule'))
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SM_CubeConvex'))
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SM_CubeSuffix'))
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SM_CubeNoSuffix'))
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SM_Sphere'))

        # delete all the assets created by the import
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')
    
    def tearDown(self):
        """
        This method is called after all of the methods in this unit test are run.
        """
        # restore blend file to the default test file
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'default_startup.blend'))