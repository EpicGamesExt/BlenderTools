# Copyright Epic Games, Inc. All Rights Reserved.
import os
import bpy
import unittest
import unreal_utilities


# TODO add github feature issue link
class Send2UeStaticMeshTestCases(unittest.TestCase):

    def setUp(self):
        """
        This method is called before any of the methods in this unit test are run.
        """
        # load in the file you will run tests on
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'static_meshes.blend'))

        # enable the required addons
        bpy.ops.preferences.addon_enable(module='send2ue')

    def test_send_cube_to_unreal(self):
        """
        This method sends a static cube mesh to unreal.
        """
        cube = bpy.data.objects['Cube']

        # move the cube to the mesh collection
        bpy.data.collections['Mesh'].objects.link(cube)
        bpy.context.scene.collection.objects.unlink(cube)

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the cube exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/Cube'))

        # delete all the assets created by the import
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')

        # move the cube out of the mesh collection
        bpy.context.scene.collection.objects.link(cube)
        bpy.data.collections['Mesh'].objects.unlink(cube)

    def test_send_mannequin_to_unreal(self):
        """
        This method sends a static mannequin mesh to unreal.
        """
        mannequin = bpy.data.objects['SK_Mannequin']

        # move the mannequin to the mesh collection
        bpy.data.collections['Mesh'].objects.link(mannequin)
        bpy.context.scene.collection.objects.unlink(mannequin)

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the mannequin exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SK_Mannequin'))

        # delete all the assets created by the import
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')

        # move the mannequin out of the mesh collection
        bpy.context.scene.collection.objects.link(mannequin)
        bpy.data.collections['Mesh'].objects.unlink(mannequin)

    def tearDown(self):
        """
        This method is called after all of the methods in this unit test are run.
        """
        # restore blend file to the default test file
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'default_startup.blend'))