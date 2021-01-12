# Copyright Epic Games, Inc. All Rights Reserved.
import os
import bpy
import unittest
import unreal_utilities


class Send2UeStaticMeshSocketsTestCases(unittest.TestCase):
    """
    related issue:
    https://github.com/EpicGames/BlenderTools/issues/69
    This tests to make sure sockets are importing correctly.
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

    def test_socket_import_true(self):
        """
        This method sends a static cube mesh with a socket to unreal.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.import_sockets = True

        cube = bpy.data.objects['Cube']

        # move the cube to the mesh collection
        bpy.data.collections['Mesh'].objects.link(cube)
        bpy.context.scene.collection.objects.unlink(cube)

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the cube in the unreal project has the given socket
        self.assertTrue(unreal_utilities.has_socket('/Game/untitled_category/untitled_asset/Cube', 'socket01'))

        # delete all the assets created by the import
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')

        # move the cube out of the mesh collection
        bpy.context.scene.collection.objects.link(cube)
        bpy.data.collections['Mesh'].objects.unlink(cube)

    def test_socket_import_false(self):
        """
        This method sends a static cube mesh without a socket to unreal.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.import_sockets = False

        cube = bpy.data.objects['Cube']

        # move the cube to the mesh collection
        bpy.data.collections['Mesh'].objects.link(cube)
        bpy.context.scene.collection.objects.unlink(cube)

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the cube in the unreal project has the given socket
        self.assertFalse(unreal_utilities.has_socket('/Game/untitled_category/untitled_asset/Cube', 'socket01'))

        # delete all the assets created by the import
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')

        # move the cube out of the mesh collection
        bpy.context.scene.collection.objects.link(cube)
        bpy.data.collections['Mesh'].objects.unlink(cube)
