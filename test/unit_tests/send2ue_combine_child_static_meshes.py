# Copyright Epic Games, Inc. All Rights Reserved.
import os
import bpy
import unittest
import unreal_utilities


class Send2UeCombineChildStaticMeshesTestCases(unittest.TestCase):
    """
    related issue:
    https://github.com/EpicGames/BlenderTools/issues/70
    This feature, give the option whether or not to join meshes in a hierarchy on import.
    """

    def setUp(self):
        # load in the file you will run tests on
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'static_meshes.blend'))

        # enable the required addons
        bpy.ops.preferences.addon_enable(module='send2ue')

        # Make sure the import area is clean
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')

        cube = bpy.data.objects['Cube']
        mannequin = bpy.data.objects['SK_Mannequin']

        # make the mannequin the parent mesh
        cube.parent = mannequin

        # move the cube to the mesh collection
        bpy.data.collections['Mesh'].objects.link(cube)
        bpy.context.scene.collection.objects.unlink(cube)

        # move the mannequin to the mesh collection
        bpy.data.collections['Mesh'].objects.link(mannequin)
        bpy.context.scene.collection.objects.unlink(mannequin)

    def tearDown(self):
        # restore blend file to the default test file
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'default_startup.blend'))

    def test_combine_child_meshes_false(self):
        """
        Sends a static mannequin and cube mesh over to unreal with combine_child_meshes property off.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences

        # turn the property off
        properties.combine_child_meshes = False

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if both the mannequin and cube exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SK_Mannequin'))
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/Cube'))

        # delete all the assets created by the import
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')

    def test_combine_child_meshes_true(self):
        """
        Sends a static mannequin and cube mesh over to unreal with combine_child_meshes property on.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences

        # turn the property on
        properties.combine_child_meshes = True

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if only the mannequin exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SK_Mannequin'))
        self.assertFalse(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/Cube'))

        # delete all the assets created by the import
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')
