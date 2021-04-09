# Copyright Epic Games, Inc. All Rights Reserved.
import os
import bpy
import unittest
import unreal_utilities


class Send2UeLODs(unittest.TestCase):
    """
    related issue:
    https://github.com/EpicGames/BlenderTools/issues/173
    """

    def setUp(self):
        # load in the file you will run tests on
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'lods.blend'))

        # enable the required addons
        bpy.ops.preferences.addon_enable(module='send2ue')

        # Make sure the import area is clean
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')

    def tearDown(self):
        # restore blend file to the default test file
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'default_startup.blend'))

    def test_static_mesh_lods(self):
        """
        This method sends static mesh lods and checks that they exist in unreal.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.import_lods = True

        cube_lods = [bpy.data.objects['Cube_LOD0'], bpy.data.objects['Cube_LOD1'], bpy.data.objects['Cube_LOD2']]

        # move the cube lods to the mesh collection
        for cube_lod in cube_lods:
            bpy.data.collections['Mesh'].objects.link(cube_lod)
            bpy.context.scene.collection.objects.unlink(cube_lod)

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the mesh exist in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/Cube'))

        # check that the number of lods in unreal match the number in blender
        self.assertEqual(unreal_utilities.get_lod_count('/Game/untitled_category/untitled_asset/Cube'), len(cube_lods))

    def test_static_mesh_lods_with_custom_collision(self):
        """
        This method sends static mesh lods with a custom collision and checks that they exist in unreal.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.import_lods = True

        cube_lods = [bpy.data.objects['Cube_LOD0'], bpy.data.objects['Cube_LOD1'], bpy.data.objects['Cube_LOD2']]
        # move the cube lods to the mesh collection
        for cube_lod in cube_lods:
            bpy.data.collections['Mesh'].objects.link(cube_lod)
            bpy.context.scene.collection.objects.unlink(cube_lod)

        # move the custom collision in the collision mesh
        custom_collision_mesh = bpy.data.objects['UCX_Cube_LOD0']
        bpy.data.collections['Collision'].objects.link(custom_collision_mesh)
        bpy.context.scene.collection.objects.unlink(custom_collision_mesh)

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the mesh exist in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/Cube'))

        # check if the asset has a custom collision
        self.assertTrue(unreal_utilities.has_custom_collision('/Game/untitled_category/untitled_asset/Cube'))

        # check that the number of lods in unreal match the number in blender
        self.assertEqual(unreal_utilities.get_lod_count('/Game/untitled_category/untitled_asset/Cube'), len(cube_lods))

    def test_skeletal_mesh_lods(self):
        """
        This method sends static mesh lods and checks that they exist in unreal.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.import_lods = True

        mannequin_lods = [
            bpy.data.objects['SK_Mannequin_LOD0'],
            bpy.data.objects['SK_Mannequin_LOD1'],
            bpy.data.objects['SK_Mannequin_LOD2'],
            bpy.data.objects['SK_Mannequin_LOD3']
        ]

        # move the cube lods to the mesh collection
        for mannequin_lod in mannequin_lods:
            bpy.data.collections['Mesh'].objects.link(mannequin_lod)
            bpy.context.scene.collection.objects.unlink(mannequin_lod)

        mannequin_rig = bpy.data.objects['root']
        bpy.data.collections['Rig'].objects.link(mannequin_rig)
        bpy.context.scene.collection.objects.unlink(mannequin_rig)

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the mesh exist in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SK_Mannequin'))

        # check that the number of lods in unreal match the number in blender
        self.assertEqual(
            unreal_utilities.get_lod_count('/Game/untitled_category/untitled_asset/SK_Mannequin'),
            len(mannequin_lods)
        )
