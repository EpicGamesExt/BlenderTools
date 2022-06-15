from utils.base_test_case import BaseSend2ueTestCaseCore


class TestSend2UeCore(BaseSend2ueTestCaseCore):
    """
    Checks core features of send to unreal
    """
    def test_property_names(self):
        """
        Checks if all the property names are unique and not empty.
        """
        self.blender.check_property_attribute(self.addon_name, 'name')

    def test_property_descriptions(self):
        """
        Checks if all the property descriptions are unique and not empty.
        """
        self.blender.check_property_attribute(self.addon_name, 'description')

    def test_extensions(self):
        """
        Checks that extensions load and function properly.
        """
        self.run_extension_tests({
            'external': {
                'example': {
                    'properties': {'hello_property': 'Hello world'},
                    'tasks': [
                        ['extensions.example.post_operation', []],
                        ['extensions.example.pre_operation', []],
                        ['extensions.example.pre_validations', []]
                    ],
                    'draws': [
                        'extensions.example.draw_validations'
                    ]
                },
            },
            'default': {
                'ue2rigify': {
                    'tasks': [
                        ['extensions.ue2rigify.pre_validations', []]
                    ]
                }
            }
        })

        # A one off test against the ./test_files/send2ue_extensions/example.py extension
        value = self.blender.get_addon_property('scene', self.addon_name, 'unreal_mesh_folder_path')
        self.assertEqual(
            value,
            '/Game/example_extension/test/',
            f'The unreal mesh folder "{value}" does not match the value it is set to in the example extension file'
        )

    def test_templates(self):
        """
        Checks that templates load, export, and update, properly.
        """
        self.run_template_tests({
            'default.json': {
                'validate_materials': False,
                'validate_textures': False,
                'import_lods': False,
                'blender.export_method.fbx.geometry.mesh_smooth_type': 'OFF',
                'unreal.import_method.fbx.skeletal_mesh_import_data.normal_generation_method': (
                    'unreal.FBXNormalGenerationMethod.MIKK_T_SPACE'
                ),
            },
            'template_1.json': {
                'validate_materials': True,
                'validate_textures': True,
                'import_lods': True,
                'blender.export_method.fbx.geometry.mesh_smooth_type': 'FACE',
                'unreal.import_method.fbx.skeletal_mesh_import_data.normal_generation_method': (
                    'unreal.FBXNormalGenerationMethod.BUILT_IN'
                ),
            }
        })

    def test_auto_create_collections(self):
        """
        Check that the auto creating collections option works.
        https://github.com/EpicGames/BlenderTools/issues/115
        """
        collection_name = self.send2ue.constants.ToolInfo.EXPORT_COLLECTION.value

        # check with automatic collections turned on
        self.blender.set_addon_property('preferences', self.addon_name, 'automatically_create_collections', True)
        self.setUp()
        self.assertTrue(
            self.blender.has_data_block('collections', collection_name),
            f'The collection "{collection_name}" does not exist when it should.'
        )

        # check with automatic collections turned off
        self.blender.set_addon_property('preferences', self.addon_name, 'automatically_create_collections', False)
        self.setUp()
        self.assertFalse(
            self.blender.has_data_block('collections', collection_name),
            f'The collection "{collection_name}" exists when it should not.'
        )
