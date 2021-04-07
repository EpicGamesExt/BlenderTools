# Copyright Epic Games, Inc. All Rights Reserved.
import os
import bpy
import unittest
import unreal_utilities


class Send2UeCollections(unittest.TestCase):
    """
    related issue:
    https://github.com/EpicGames/BlenderTools/issues/249
    This feature allows swapping out meshes on existing skeletons.
    """

    def setUp(self):
        # load in the file you will run tests on
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'skeletal_meshes.blend'))

        # enable the required addons
        bpy.ops.preferences.addon_enable(module='send2ue')
        bpy.ops.preferences.addon_enable(module='ue2rigify')
        bpy.ops.preferences.addon_enable(module='rigify')

    def tearDown(self):
        # restore blend file to the default test file
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'default_startup.blend'))

    def test_import_on_existing_skeleton(self):
        """
        This method sends a skeletal mannequin mesh with animation to unreal.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences

        mannequin = bpy.data.objects['SK_Mannequin']
        mannequin_rig = bpy.data.objects['root']

        # move the mannequin mesh to the mesh collection
        bpy.data.collections['Mesh'].objects.link(mannequin)
        bpy.context.scene.collection.objects.unlink(mannequin)

        # move the mannequin rig to the rig collection
        bpy.data.collections['Rig'].objects.link(mannequin_rig)
        bpy.context.scene.collection.objects.unlink(mannequin_rig)

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # delete the skeletal mesh
        unreal_utilities.delete_asset('/Game/untitled_category/untitled_asset/SK_Mannequin')

        # delete the animation directory
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset/animations')

        properties.unreal_mesh_folder_path = '/Game/test/'
        properties.unreal_skeleton_asset_path = '/Game/untitled_category/untitled_asset/SK_Mannequin_Skeleton'

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the mannequin skeletal mesh exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/test/SK_Mannequin'))

        # check that the mannequin skeleton does not exist in the unreal project
        self.assertFalse(unreal_utilities.asset_exists('/Game/test/SK_Mannequin_Skeleton'))

        # check if the mannequin animation exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/animations/third_person_run_01'
        ))
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/animations/third_person_walk_01'
        ))

        # delete all the assets created by the import
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')
        unreal_utilities.delete_directory('/Game/test')
