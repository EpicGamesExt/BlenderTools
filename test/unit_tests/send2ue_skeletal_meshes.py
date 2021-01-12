# Copyright Epic Games, Inc. All Rights Reserved.
import os
import bpy
import unittest
import unreal_utilities


class Send2UeSkeletalMeshTestCases(unittest.TestCase):
    """
    related issue:
    https://github.com/EpicGames/BlenderTools
    ^ This is a core addon feature, but if this feature was created based off an issue, a link to the issue
    should be left is the docstring.
    """

    def setUp(self):
        # load in the file you will run tests on
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'skeletal_meshes.blend'))

        # enable the required addons
        bpy.ops.preferences.addon_enable(module='send2ue')
        bpy.ops.preferences.addon_enable(module='ue2rigify')
        bpy.ops.preferences.addon_enable(module='rigify')

        # Make sure the import area is clean
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')

    def tearDown(self):
        # restore blend file to the default test file
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'default_startup.blend'))

    def test_send_cube_rig_to_unreal(self):
        """
        This method sends a skeletal cube mesh with animation to unreal.
        """
        cube = bpy.data.objects['Cube']
        cube_rig = bpy.data.objects['Armature']

        # move the cube mesh to the mesh collection
        bpy.data.collections['Mesh'].objects.link(cube)
        bpy.context.scene.collection.objects.unlink(cube)

        # move the cube rig to the rig collection
        bpy.data.collections['Rig'].objects.link(cube_rig)
        bpy.context.scene.collection.objects.unlink(cube_rig)

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the cube skeletal mesh exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/Cube'))

        # check if the cube skeleton exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/Cube_Skeleton'))

        # check if the cube animation exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/animations/cube_bend_01'
        ))

        # delete all the assets created by the import
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')

        # move the cube out of the mesh collection
        bpy.context.scene.collection.objects.link(cube)
        bpy.data.collections['Mesh'].objects.unlink(cube)

        # move the cube rig out of the rig collection
        bpy.context.scene.collection.objects.link(cube_rig)
        bpy.data.collections['Rig'].objects.unlink(cube_rig)

    def test_send_mannequin_rig_to_unreal(self):
        """
        This method sends a skeletal mannequin mesh with animation to unreal.
        """
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

        # check if the mannequin skeletal mesh exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SK_Mannequin'))

        # check if the mannequin skeleton exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SK_Mannequin_Skeleton'))

        # check if the mannequin animation exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/animations/third_person_run_01'
        ))
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/animations/third_person_walk_01'
        ))

        # delete all the assets created by the import
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')

        # move the mannequin out of the mesh collection
        bpy.context.scene.collection.objects.link(mannequin)
        bpy.data.collections['Mesh'].objects.unlink(mannequin)

        # move the mannequin rig out of the rig collection
        bpy.context.scene.collection.objects.link(mannequin_rig)
        bpy.data.collections['Rig'].objects.unlink(mannequin_rig)

    def test_send_ue2rigify_mannequin_rig_to_unreal(self):
        """
        This method sends a skeletal mannequin mesh with animation to unreal that is in the ue2rigify control mode.
        """
        mannequin = bpy.data.objects['SK_Mannequin']
        mannequin_rig = bpy.data.objects['root']

        # move the mannequin mesh to the mesh collection
        bpy.data.collections['Mesh'].objects.link(mannequin)
        bpy.context.scene.collection.objects.unlink(mannequin)

        # move the mannequin rig to the rig collection
        bpy.data.collections['Rig'].objects.link(mannequin_rig)
        bpy.context.scene.collection.objects.unlink(mannequin_rig)

        # unfreeze the rig
        bpy.context.window_manager.ue2rigify.freeze_rig = False

        # set the source rig
        bpy.context.window_manager.ue2rigify.source_rig_name = 'root'

        # convert the source rig to a control rig
        bpy.ops.ue2rigify.convert_to_control_rig()

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the mannequin skeletal mesh exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SK_Mannequin'))

        # check if the mannequin skeleton exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SK_Mannequin_Skeleton'))

        # check if the mannequin animation exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/animations/third_person_run_01'
        ))
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/animations/third_person_walk_01'
        ))

        # delete all the assets created by the import
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')

        # revert the source rig back to a control rig
        bpy.ops.ue2rigify.revert_to_source_rig()

        # move the mannequin out of the mesh collection
        bpy.context.scene.collection.objects.link(mannequin)
        bpy.data.collections['Mesh'].objects.unlink(mannequin)

        # move the mannequin rig out of the rig collection
        bpy.context.scene.collection.objects.link(mannequin_rig)
        bpy.data.collections['Rig'].objects.unlink(mannequin_rig)
