# Copyright Epic Games, Inc. All Rights Reserved.
import os
import bpy
import unittest


class Send2UeGeneralTestCases(unittest.TestCase):
    """
    related issues:
    https://github.com/EpicGames/BlenderTools/issues/115
    Automatically create collections as new folders when exporting to Unreal.
    """
    def setUp(self):
        # enable the required addons
        bpy.ops.preferences.addon_enable(module='send2ue')

    def tearDown(self):
        # restore blend file to the default test file
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'default_startup.blend'))
        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.automatically_create_collections = True

    def test_predefined_collections_automatically_created(self):
        """
        Checks for the presence of the pre-defined collections that the addon automatically creates.
        """

        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.automatically_create_collections = True

        # Reload home file to see re-run the automatic collection creation
        bpy.ops.wm.read_homefile()

        for coll in properties.collection_names:
            self.assertTrue(bpy.data.collections.get(coll))

    def test_predefined_collections_not_created(self):
        """
        Checks that the pre-defined collections haven't been automatically created by the addon.
        """

        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.automatically_create_collections = False

        # Reload home file to see if automatic collection creation is disabled
        bpy.ops.wm.read_homefile()

        for coll in properties.collection_names:
            self.assertFalse(bpy.data.collections.get(coll))
