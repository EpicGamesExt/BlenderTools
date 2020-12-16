# Copyright Epic Games, Inc. All Rights Reserved.
import os
import bpy
import unittest
import unreal_utilities


class Send2UeMaterialToUnreal(unittest.TestCase):
    """
    related issue:
    https://github.com/EpicGames/BlenderTools
    ^ This is a core addon feature, but if this feature was created based off an issue, a link to the issue
    should be left is the docstring.
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

        # Cleanup the import area after we are done.
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')

    def test_send_material_to_unreal_true(self):
        """
        This method sends a cube with a material to unreal
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.import_materials = True

        cube = bpy.data.objects['Cube']

        # move the cube to the mesh collection
        bpy.data.collections['Mesh'].objects.link(cube)
        bpy.context.scene.collection.objects.unlink(cube)

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the cube and material exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/Cube'))
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/Material'))

        # move the cube out of the mesh collection
        bpy.context.scene.collection.objects.link(cube)
        bpy.data.collections['Mesh'].objects.unlink(cube)

    def test_send_material_to_unreal_false(self):
        """
        This method sends a cube without a material to unreal
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.import_materials = False

        cube = bpy.data.objects['Cube']

        # move the cube to the mesh collection
        bpy.data.collections['Mesh'].objects.link(cube)
        bpy.context.scene.collection.objects.unlink(cube)

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the cube exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/Cube'))
        # make sure the material does not exist in the unreal project
        self.assertFalse(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/Material'))

        # move the cube out of the mesh collection
        bpy.context.scene.collection.objects.link(cube)
        bpy.data.collections['Mesh'].objects.unlink(cube)
