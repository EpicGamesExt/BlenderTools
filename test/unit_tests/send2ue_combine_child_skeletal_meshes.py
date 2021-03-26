# Copyright Epic Games, Inc. All Rights Reserved.
import os
import bpy
import bmesh
import unittest
import unreal_utilities


class Send2UeCombineChildSkeletalMeshesTestCases(unittest.TestCase):
    """
    related issue:
    https://github.com/EpicGames/BlenderTools/issues/70
    This feature, give the option whether or not to join meshes in a hierarchy on import.
    """
    @staticmethod
    def split_up_object(mesh_object):
        """
        This function splits the given mesh object into multiple objects.

        :param object mesh_object: A mesh object:
        """
        # select the mesh
        bpy.ops.object.select_all(action='DESELECT')
        mesh_object.select_set(True)
        bpy.context.view_layer.objects.active = mesh_object

        # switch to edit mode
        bpy.ops.object.mode_set(mode='EDIT')
        mesh = bpy.context.edit_object.data
        bmesh_object = bmesh.from_edit_mesh(mesh)

        # deselect all vertices but one
        bmesh_object.verts.ensure_lookup_table()
        for vert in bmesh_object.verts:
            vert.select = False
        bmesh_object.verts[0].select = True
        bmesh.update_edit_mesh(mesh)

        # selected the linked vertices
        bpy.ops.mesh.select_linked()

        # separate the selection into another object
        bpy.ops.mesh.separate(type='SELECTED')

    def setUp(self):
        # load in the file you will run tests on
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'skeletal_meshes.blend'))

        # enable the required addons
        bpy.ops.preferences.addon_enable(module='send2ue')

        # Make sure the import area is clean
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')

        rig = bpy.data.objects['root']
        mannequin_mesh = bpy.data.objects['SK_Mannequin']

        # move the cube to the mesh collection
        bpy.data.collections['Mesh'].objects.link(mannequin_mesh)
        bpy.context.scene.collection.objects.unlink(mannequin_mesh)

        # move the mannequin armature to the rig collection
        bpy.data.collections['Rig'].objects.link(rig)
        bpy.context.scene.collection.objects.unlink(rig)

        # split the mannequin mesh object into multiple mesh objects
        self.split_up_object(mannequin_mesh)

    def tearDown(self):
        # delete all the assets created by the import
        unreal_utilities.delete_directory('/Game/untitled_category/untitled_asset')

        # restore blend file to the default test file
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'default_startup.blend'))

    def test_combine_child_meshes_false(self):
        """
        Sends a multi mesh character over with the combine_child_meshes property off.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences

        # turn the property off
        properties.combine_child_meshes = False

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if both the mannequin meshes exist in the unreal project
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/SK_Mannequin'
        ))
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/SK_Mannequin_Skeleton'
        ))

        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/SK_Mannequin_001'
        ))
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/SK_Mannequin_001_Skeleton'
        ))

    def test_combine_child_meshes_true(self):
        """
        Sends a multi mesh character over with the combine_child_meshes property on.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences

        # turn the property on
        properties.combine_child_meshes = True

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if only one of the mannequin meshes exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/SK_Mannequin'
        ))
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/SK_Mannequin_Skeleton'
        ))

        self.assertFalse(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/SK_Mannequin_001'
        ))
        self.assertFalse(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/SK_Mannequin_001_Skeleton'
        ))

    def test_combine_non_child_meshes_false(self):
        """
        Sends a multi non-child mesh character over with the combine_child_meshes property off.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences

        # turn the property off
        properties.combine_child_meshes = False

        # remove all parents from the meshes while still keeping the armature modifier
        for scene_object in bpy.data.objects:
            if scene_object.type == 'MESH':
                scene_object.parent = None

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if both the mannequin meshes exist in the unreal project
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/SK_Mannequin'
        ))
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/SK_Mannequin_Skeleton'
        ))

        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/SK_Mannequin_001'
        ))
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/SK_Mannequin_001_Skeleton'
        ))

    def test_combine_non_child_meshes_true(self):
        """
        Sends a multi non-child mesh character over with the combine_child_meshes property on.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences

        # turn the property on
        properties.combine_child_meshes = True

        # remove all parents from the meshes while still keeping the armature modifier
        for scene_object in bpy.data.objects:
            if scene_object.type == 'MESH':
                scene_object.parent = None

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if only one of the mannequin meshes exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/SK_Mannequin'
        ))
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/SK_Mannequin_Skeleton'
        ))

        self.assertFalse(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/SK_Mannequin_001'
        ))
        self.assertFalse(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/SK_Mannequin_001_Skeleton'
        ))

    def test_combine_child_meshes_using_collection_name(self):
        """
        Sends a multi mesh character over with the combine_child_meshes and use_immediate_parent_collection_name
        properties on.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences

        # turn the properties on
        properties.combine_child_meshes = True
        properties.use_immediate_parent_collection_name = True

        # get mannequin meshes
        mannequin_mesh = bpy.data.objects['SK_Mannequin']
        mannequin_mesh_001 = bpy.data.objects['SK_Mannequin.001']

        # create a collection in the mesh collection
        test_collection = bpy.data.collections.new('test')
        bpy.data.collections['Mesh'].children.link(test_collection)

        # move the mannequin meshes into the new collection
        test_collection.objects.link(mannequin_mesh)
        test_collection.objects.link(mannequin_mesh_001)

        # run the send to unreal operation
        bpy.ops.wm.send2ue()

        # check if only one of the mannequin meshes exists in the unreal project
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/test'
        ))
        self.assertTrue(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/test_Skeleton'
        ))

        self.assertFalse(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/SK_Mannequin'
        ))
        self.assertFalse(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/SK_Mannequin_Skeleton'
        ))

        self.assertFalse(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/SK_Mannequin_001'
        ))
        self.assertFalse(unreal_utilities.asset_exists(
            '/Game/untitled_category/untitled_asset/SK_Mannequin_001_Skeleton'
        ))
