# Copyright Epic Games, Inc. All Rights Reserved.
import os
import bpy
import unittest
import unreal_utilities


class Send2UeStaticMeshTestCases(unittest.TestCase):
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

    def test_send_cube_to_unreal_with_affixes_added_permanently(self):
        """
        This method sends a static cube mesh to unreal with affixes added permanently in Blender.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences
        cube = bpy.data.objects['Cube']

        # move the cube to the mesh collection
        bpy.data.collections['Mesh'].objects.link(cube)
        bpy.context.scene.collection.objects.unlink(cube)

        # turn on the use affixes option
        properties.auto_add_asset_name_affixes = True

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the cube exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SM_Cube'), "Cube static mesh was not prefixed by SM_")
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/M_Material'), "Material was not prefixed by M_")
        self.assertTrue(cube.name == "SM_Cube", "Cube was not renamed to SM_Cube in Blender")

        # delete all the assets created by the import
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')

        # turn off the use affixes option
        properties.auto_add_asset_name_affixes = False

        # move the cube out of the mesh collection
        bpy.context.scene.collection.objects.link(cube)
        bpy.data.collections['Mesh'].objects.unlink(cube)

    def test_send_cube_to_unreal_with_affixes_removed_after_export(self):
        """
        This method sends a static cube mesh to unreal with affixes added automatically before export and removed after.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences
        cube = bpy.data.objects['Cube']

        # move the cube to the mesh collection
        bpy.data.collections['Mesh'].objects.link(cube)
        bpy.context.scene.collection.objects.unlink(cube)

        # turn on the use affixes option
        properties.auto_add_asset_name_affixes = True
        properties.auto_remove_original_asset_names = True

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the cube exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SM_Cube'), "Cube static mesh was not prefixed by SM_")
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/M_Material'), "Material was not prefixed by M_")
        self.assertTrue(cube.name == "Cube", "Prefix of Cube was not removed after export in Blender")

        # delete all the assets created by the import
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')

        # turn off the use affixes option
        properties.auto_add_asset_name_affixes = False
        properties.auto_remove_original_asset_names = False

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
