import unittest
import os
from utils.base_test_case import BaseSend2ueTestCaseCore, SkipSend2UeTests
from test_send2ue_cubes import TestSend2UeCubes


class TestSend2UeExtensionExampleCubes(SkipSend2UeTests, TestSend2UeCubes, BaseSend2ueTestCaseCore):
    """
    Runs several test cases with the affix extension on the cube meshes.
    """
    def setUp(self):
        super().setUp()
        self.set_extension_repo(os.path.join(self.test_folder, 'test_files', 'send2ue_extensions'))
        self.blender.set_addon_property('scene', 'send2ue', 'extensions.example.use_example_extension', True)

    def test_extension(self):
        """
        Checks that the example extension load and function properly.
        """
        self.run_extension_tests({
            'external': {
                'example': {
                    'properties': {'hello_property': 'Hello world'},
                    'tasks': [
                        'post_operation',
                        'pre_operation',
                        'pre_validations'
                    ],
                    'draws': [
                        'draw_validations'
                    ]
                },
            }
        })

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
