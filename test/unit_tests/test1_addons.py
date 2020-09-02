# Copyright Epic Games, Inc. All Rights Reserved.
import bpy
import unittest


# TODO add github feature issue link
class AddonTestCases(unittest.TestCase):

    def test_is_send2ue_enabled(self):
        self.assertTrue(bool(bpy.context.preferences.addons.get('send2ue')))

    def test_is_ue2rigify_enabled(self):
        self.assertTrue(bool(bpy.context.preferences.addons.get('ue2rigify')))