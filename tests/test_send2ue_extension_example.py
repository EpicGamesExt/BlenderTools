import unittest
import os
from utils.base_test_case import BaseSend2ueTestCaseCore
from test_send2ue_cubes import TestSend2UeCubes


class TestSend2UeExtensionExampleCubes(TestSend2UeCubes, BaseSend2ueTestCaseCore):
    """
    Runs several test cases with the affix extension on the cube meshes.
    """
    def setUp(self):
        super().setUp()
        self.set_extension_repo(os.path.join(self.test_folder, 'test_files', 'send2ue_extensions'))
        self.blender.set_addon_property('scene', 'send2ue', 'extensions.example.use_example_extension', True)

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

    def test_extension(self):
        """
        Checks that extensions load and function properly.
        """
        self.run_extension_tests({
            'external': {
                'example': {
                    'properties': {'hello_property': 'Hello world'},
                    'tasks': [
                        'extensions.example.post_operation',
                        'extensions.example.pre_operation',
                        'extensions.example.pre_validations'
                    ],
                    'draws': [
                        'extensions.example.draw_validations'
                    ]
                },
            }
        })

    @unittest.skip
    def test_import_asset_operator(self):
        pass

    def test_default_send_to_unreal(self):
        """
        Sends a cube mesh with default settings.
        """
        self.move_to_collection(['Cube1_LOD0'], 'Export')
        self.send2ue_operation()
        self.assert_mesh_import('Cube1_LOD0_added_this_renamed_again')

        # A one off test against the ./test_files/send2ue_extensions/example.py extension
        value = self.blender.get_addon_property('scene', self.addon_name, 'unreal_mesh_folder_path')
        self.assertEqual(
            value,
            '/Game/example_extension/test/',
            f'The unreal mesh folder "{value}" does not match the value it is set to in the example extension file'
        )
