# Copyright Epic Games, Inc. All Rights Reserved.
import os
import bpy
import unittest
import unreal_utilities


class Send2UePathsTestCases(unittest.TestCase):
    """
    related issues:
    https://github.com/EpicGames/BlenderTools/issues/183
    Automatically create collections as new folders when exporting to Unreal.

    https://github.com/EpicGames/BlenderTools/issues/202
    Ability to set the name of imported combined skeletal mesh
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

        # get mannequin mesh and rig
        mannequin_mesh = bpy.data.objects['SK_Mannequin']
        mannequin_rig = bpy.data.objects['root']

        # create 3 collections all as children of each other
        previous_collection = None
        for collection_name in ['test1', 'test2', 'test3']:
            test_collection = bpy.data.collections.new(collection_name)
            if not previous_collection:
                bpy.data.collections['Mesh'].children.link(test_collection)
            else:
                previous_collection.children.link(test_collection)

            previous_collection = test_collection

        # move the mannequin meshes into the lowest collection
        previous_collection.objects.link(mannequin_mesh)
        bpy.context.scene.collection.objects.unlink(mannequin_mesh)

        # move the mannequin rig to the rig collection
        bpy.data.collections['Rig'].objects.link(mannequin_rig)
        bpy.context.scene.collection.objects.unlink(mannequin_rig)

    def tearDown(self):
        # restore blend file to the default test file
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'default_startup.blend'))
        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.use_immediate_parent_collection_name = False
        properties.use_collections_as_folders = False

    def test_no_sub_collections_folder_collection_true_immediate_true(self):
        """
        Sends a skeletal mesh not under a sub collection hierarchy with use_immediate_parent_collection_name as true
        and use_collections_as_folders as true.
        """

        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.use_immediate_parent_collection_name = True
        properties.use_collections_as_folders = True

        # get mannequin mesh and rig
        mannequin_mesh = bpy.data.objects['SK_Mannequin']

        # move the mannequin meshes into the top collection
        bpy.data.collections['Mesh'].objects.link(mannequin_mesh)
        bpy.data.collections['test3'].objects.unlink(mannequin_mesh)

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

    def test_sub_collections_folder_collection_true_immediate_true(self):
        """
        Sends a skeletal mesh under a sub collection hierarchy with use_immediate_parent_collection_name as true
        and use_collections_as_folders as true.
        """
        # turn the properties on
        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.use_immediate_parent_collection_name = True
        properties.use_collections_as_folders = True

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if only one of the mannequin meshes exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/test1/test2/test3'
        ))
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/test1/test2/test3_Skeleton'
        ))

        # check if the mannequin animation exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/animations/third_person_run_01'
        ))
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/animations/third_person_walk_01'
        ))

    def test_sub_collections_folder_collection_true_immediate_false(self):
        """
        Sends a skeletal mesh under a sub collection hierarchy with use_immediate_parent_collection_name as false
        and use_collections_as_folders as true.
        """
        # turn the properties on
        properties = bpy.context.preferences.addons['send2ue'].preferences
        properties.use_collections_as_folders = True
        properties.use_immediate_parent_collection_name = False

        test_collection = bpy.data.collections.new('test4')
        bpy.data.collections['test2'].children.link(test_collection)

        cube = bpy.data.objects['Cube']
        cube_rig = bpy.data.objects['Armature']

        test_collection.objects.link(cube)
        bpy.data.collections['Rig'].objects.link(cube_rig)
        bpy.context.scene.collection.objects.unlink(cube_rig)

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if only one of the mannequin meshes exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/test1/test2/test3/SK_Mannequin'
        ))
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/test1/test2/test3/SK_Mannequin_Skeleton'
        ))

        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/test1/test2/test4/Cube'
        ))
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/test1/test2/test4/Cube_Skeleton'
        ))

        # check if the mannequin animation exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/animations/third_person_run_01'
        ))
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/animations/third_person_walk_01'
        ))

        # check if the cube animation exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/animations/cube_bend_01'
        ))
