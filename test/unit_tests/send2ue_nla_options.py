# Copyright Epic Games, Inc. All Rights Reserved.
import os
import bpy
import unittest
import unreal_utilities


class Send2UeNlaOptionsTestCases(unittest.TestCase):
    """
    related issue:
    https://github.com/EpicGames/BlenderTools/issues/99
    This class checks all the export options related to the NLA strips.
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

        source_rig = bpy.data.objects['root']
        mannequin = bpy.data.objects['SK_Mannequin']

        # move the mannequin mesh to the mesh collection
        bpy.data.collections['Mesh'].objects.link(mannequin)
        bpy.context.scene.collection.objects.unlink(mannequin)

        # move the mannequin rig to the rig collection
        bpy.data.collections['Rig'].objects.link(source_rig)
        bpy.context.scene.collection.objects.unlink(source_rig)

    def tearDown(self):
        # restore blend file to the default test file
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'default_startup.blend'))

    def test_auto_stash_active_action_false(self):
        """
        This method tests that only stashed nla strips are exported when auto_stash_active_action is set to false.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.export_all_actions = True
        properties.auto_stash_active_action = False
        properties.auto_sync_control_nla_to_source = True

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the mannequin skeletal mesh exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SK_Mannequin'))

        # check if the mannequin skeleton exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SK_Mannequin_Skeleton'))

        # check if the run animation exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/animations/third_person_run_01'
        ))
        # check if the walk animation exists in the unreal project
        self.assertFalse(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/animations/third_person_walk_01'
        ))

    def test_export_all_actions_false(self):
        """
        This method tests that only un-muted animations are exported when export_all_actions is set to false.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.export_all_actions = False
        properties.auto_stash_active_action = True
        properties.auto_sync_control_nla_to_source = True

        source_rig = bpy.data.objects['root']

        # mute the walk animation
        source_rig.animation_data.nla_tracks['third_person_run_01'].mute = True

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the mannequin skeletal mesh exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SK_Mannequin'))

        # check if the mannequin skeleton exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SK_Mannequin_Skeleton'))

        # check if the run animation exists in the unreal project
        self.assertFalse(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/animations/third_person_run_01'
        ))
        # check if the walk animation exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/animations/third_person_walk_01'
        ))

    def test_auto_sync_control_nla_to_source_false(self):
        """
        This method tests that no animations are synced over when auto_sync_control_nla_to_source is set to false.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.export_all_actions = True
        properties.auto_stash_active_action = True
        properties.auto_sync_control_nla_to_source = False

        # unfreeze the rig
        bpy.context.window_manager.ue2rigify.freeze_rig = False

        # set the source rig
        bpy.context.window_manager.ue2rigify.source_rig_name = 'root'

        # convert the source rig to a control rig
        bpy.ops.ue2rigify.convert_to_control_rig()

        # remove animation data from the source rig
        source_rig = bpy.data.objects['root']
        source_rig.animation_data_clear()

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the mannequin skeletal mesh exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SK_Mannequin'))

        # check if the mannequin skeleton exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SK_Mannequin_Skeleton'))

        # check if the run animation exists in the unreal project
        self.assertFalse(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/animations/third_person_run_01'
        ))
        # check if the walk animation exists in the unreal project
        self.assertFalse(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/animations/third_person_walk_01'
        ))

        # revert the source rig back to a control rig
        bpy.ops.ue2rigify.revert_to_source_rig()

    def test_export_solo_action(self):
        """
        This method tests that if a NLA track is starred that only that track's action is exported.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.export_all_actions = False
        properties.auto_stash_active_action = True
        properties.auto_sync_control_nla_to_source = True

        source_rig = bpy.data.objects['root']

        # set the walk animation to solo
        source_rig.animation_data.nla_tracks['third_person_run_01'].is_solo = True

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the mannequin skeletal mesh exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SK_Mannequin'))

        # check if the mannequin skeleton exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SK_Mannequin_Skeleton'))

        # check if the run animation exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/animations/third_person_run_01'
        ))
        # check if the walk animation exists in the unreal project
        self.assertFalse(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/animations/third_person_walk_01'
        ))

    def test_export_control_rig_solo_action(self):
        """
        This method tests that if a NLA track is starred on the control rig that only that track's action is exported.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.export_all_actions = False
        properties.auto_stash_active_action = True
        properties.auto_sync_control_nla_to_source = True

        # unfreeze the rig
        bpy.context.window_manager.ue2rigify.freeze_rig = False

        # set the source rig
        bpy.context.window_manager.ue2rigify.source_rig_name = 'root'

        # convert the source rig to a control rig
        bpy.ops.ue2rigify.convert_to_control_rig()

        control_rig = bpy.data.objects['rig']

        # set the walk animation to solo
        control_rig.animation_data.nla_tracks['third_person_run_01'].is_solo = True

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if the mannequin skeletal mesh exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SK_Mannequin'))

        # check if the mannequin skeleton exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists('/Game/untitled_category/untitled_asset/SK_Mannequin_Skeleton'))

        # check if the run animation exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/animations/third_person_run_01'
        ))
        # check if the walk animation exists in the unreal project
        self.assertFalse(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/animations/third_person_walk_01'
        ))
