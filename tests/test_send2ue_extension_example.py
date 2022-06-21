import unittest
from utils.base_test_case import BaseSend2ueTestCaseCore
from test_send2ue_cubes import TestSend2UeCubes


class TestSend2UeExtensionExampleCubes(TestSend2UeCubes, BaseSend2ueTestCaseCore):
    """
    Runs several test cases with the affix extension on the cube meshes.
    """
    @unittest.skip
    def test_bulk_send_to_unreal(self):
        pass

    @unittest.skip
    def test_lods(self):
        pass

    @unittest.skip
    def test_sockets(self):
        pass

    @unittest.skip
    def test_collisions(self):
        pass

    @unittest.skip
    def test_use_object_origin_option(self):
        pass

    @unittest.skip
    def test_combine_child_meshes_option(self):
        pass

    @unittest.skip
    def test_use_immediate_parent_collection_name_option(self):
        pass

    @unittest.skip
    def test_use_collections_as_folders_option(self):
        pass

    @unittest.skip
    def test_materials(self):
        pass

    @unittest.skip
    def test_textures(self):
        pass

    @unittest.skip
    def test_extension(self):
        pass

    @unittest.skip
    def test_import_asset_operator(self):
        pass

    def test_default_send_to_unreal(self):
        """
        Sends a cube mesh with default settings.
        """
        self.move_to_collection(['Cube1_LOD0'], 'Export')
        self.send2ue_operation()
        self.assert_mesh_import('SM_Cube1_LOD0_added_this_renamed_again')

        # A one off test against the ./test_files/send2ue_extensions/example.py extension
        value = self.blender.get_addon_property('scene', self.addon_name, 'unreal_mesh_folder_path')
        self.assertEqual(
            value,
            '/Game/example_extension/test/',
            f'The unreal mesh folder "{value}" does not match the value it is set to in the example extension file'
        )
