# Copyright Epic Games, Inc. All Rights Reserved.
import os
import bpy
import unittest
import unreal_utilities


class Send2UeMaterialTextureTestCases(unittest.TestCase):
    """
    related issue:
    https://github.com/EpicGames/BlenderTools/issues/83
    This tests to make sure materials and textures import correctly.
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

    def test_material_with_texture_true(self):
        """
        This method sends a cube with a material and texture to unreal
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.import_materials = True
        properties.import_materials = True

        cube = bpy.data.objects['Cube']

        # move the cube to the mesh collection
        bpy.data.collections['Mesh'].objects.link(cube)
        bpy.context.scene.collection.objects.unlink(cube)

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the cube and material and its texture exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/Cube'))
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/Material'))
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/unreal-engine-logo'))

        # check to make sure the image file created from unpacking was removed
        self.assertFalse(os.path.exists(os.path.join(
            bpy.data.filepath,
            'textures',
            'unreal-engine-logo.jpg'
        )))

        # check to make sure the texture folder created from unpacking was removed
        self.assertFalse(os.path.exists(os.path.join(
            bpy.data.filepath,
            'textures'
        )))

        # move the cube out of the mesh collection
        bpy.context.scene.collection.objects.link(cube)
        bpy.data.collections['Mesh'].objects.unlink(cube)

    def test_material_with_affixed_texture_true(self):
        """
        This method sends a cube with a material and texture to unreal where the texture has been renamed.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.import_materials = True
        properties.import_materials = True

        cube = bpy.data.objects['Cube']

        # move the cube to the mesh collection
        bpy.data.collections['Mesh'].objects.link(cube)
        bpy.context.scene.collection.objects.unlink(cube)

        # turn on the use affixes option
        properties.auto_add_asset_name_affixes = True

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the cube and material and its texture exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SM_Cube'))
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/M_Material'))
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/T_unreal-engine-logo'))

        # check to make sure the image file created from unpacking was removed
        self.assertFalse(os.path.exists(os.path.join(
            bpy.data.filepath,
            'textures',
            'T_unreal-engine-logo.jpg'
        )))

        # check to make sure the texture folder created from unpacking was removed
        self.assertFalse(os.path.exists(os.path.join(
            bpy.data.filepath,
            'textures'
        )))

        # move the cube out of the mesh collection
        bpy.context.scene.collection.objects.link(cube)
        bpy.data.collections['Mesh'].objects.unlink(cube)

        # turn off the use affixes option
        properties.auto_add_asset_name_affixes = False

    def test_material_with_affixed_texture_true_affix_removed_after_export(self):
        """
        This method sends a cube with a material and texture to unreal where the texture has been renamed and the
        rename reverted back after the export.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.import_materials = True
        properties.import_materials = True

        cube = bpy.data.objects['Cube']

        # move the cube to the mesh collection
        bpy.data.collections['Mesh'].objects.link(cube)
        bpy.context.scene.collection.objects.unlink(cube)

        # turn on the use affixes option
        properties.auto_add_asset_name_affixes = True
        properties.auto_remove_original_asset_names = True

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the cube and material and its texture exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SM_Cube'))
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/M_Material'))
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/T_unreal-engine-logo'))

        # check to make sure the image file created from unpacking was removed
        self.assertFalse(os.path.exists(os.path.join(
            bpy.data.filepath,
            'textures',
            'unreal-engine-logo.jpg'
        )))

        # check to make sure the texture folder created from unpacking was removed
        self.assertFalse(os.path.exists(os.path.join(
            bpy.data.filepath,
            'textures'
        )))

        # move the cube out of the mesh collection
        bpy.context.scene.collection.objects.link(cube)
        bpy.data.collections['Mesh'].objects.unlink(cube)

        # turn off the use affixes option
        properties.auto_add_asset_name_affixes = False
        properties.auto_remove_original_asset_names = False

    def test_material_with_texture_false(self):
        """
        This method sends a cube without a material and without a texture to unreal
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.import_materials = False
        properties.import_textures = False

        cube = bpy.data.objects['Cube']

        # move the cube to the mesh collection
        bpy.data.collections['Mesh'].objects.link(cube)
        bpy.context.scene.collection.objects.unlink(cube)

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the cube exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/Cube'))
        # make sure the material and texture do not exist in the unreal project
        self.assertFalse(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/Material'))
        self.assertFalse(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/unreal-engine-logo'))

        # move the cube out of the mesh collection
        bpy.context.scene.collection.objects.link(cube)
        bpy.data.collections['Mesh'].objects.unlink(cube)
