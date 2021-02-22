# Copyright Epic Games, Inc. All Rights Reserved.
import os
import bpy
import unittest


class Ue2RigifyModesTestCases(unittest.TestCase):
    """
    related issue:
    https://github.com/EpicGames/BlenderTools
    ^ This is a core addon feature, but if this feature was created based off an issue, a link to the issue
    should be left is the docstring.
    """

    def setUp(self):
        # load in the file you will run tests on
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'skeletal_meshes.blend'))

        # disable the send2ue addon
        bpy.ops.preferences.addon_disable(module='send2ue')

        # enable the rigify addon
        bpy.ops.preferences.addon_enable(module='rigify')

        # enable the ue2rigify addon
        bpy.ops.preferences.addon_enable(module='ue2rigify')

    def tearDown(self):
        # enable the send2ue addon
        bpy.ops.preferences.addon_enable(module='send2ue')

        # restore blend file to the default test file
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'default_startup.blend'))

    def test_mode_switching(self):
        """
        This method switches from 'SOURCE' mode to 'METARIG', 'FK_TO_SOURCE', 'SOURCE_TO_DEFORM', and 'CONTROL' mode.
        """
        modes = [
            'METARIG',
            'FK_TO_SOURCE',
            'SOURCE_TO_DEFORM',
            'CONTROL',
        ]

        # un freeze the rig
        bpy.ops.ue2rigify.un_freeze_rig()

        # set the source rig object
        bpy.context.window_manager.ue2rigify.source_rig_name = 'root'

        # switch to each of the modes from source mode
        for mode in modes:
            self.assertEquals(bpy.ops.ue2rigify.switch_modes(mode=mode), {'FINISHED'})
