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
            'default': {
                'ue2rigify': {
                    'tasks': [
                        'pre_operation'
                    ]
                }
            }
        })

    def test_templates(self):
        """
        Checks that templates load, export, and update, properly.
        """
        self.run_template_tests({
            'default.json': {
                'validate_materials': False,
                'validate_textures': False,
                'import_lods': False,
                'blender.export_method.fbx.geometry.mesh_smooth_type': 'FACE',
                'unreal.import_method.fbx.skeletal_mesh_import_data.normal_generation_method': (
                    'unreal.FBXNormalGenerationMethod.MIKK_T_SPACE'
                ),
            },
            'template_1.json': {
                'validate_materials': True,
                'validate_textures': True,
                'import_lods': True,
                'blender.export_method.fbx.geometry.mesh_smooth_type': 'OFF',
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

    def test_import_asset_operator(self):
        """
        Tests that the asset import operator is working correctly.
        """
        self.run_import_asset_operator_tests({
            'ThirdPersonRun.FBX': [
                'root',
                'SK_Mannequin_LOD0',
                'SK_Mannequin_LOD1',
                'SK_Mannequin_LOD2',
                'SK_Mannequin_LOD3',
                'SK_Mannequin_LodGroup'
            ]
        })

    def test_scene_data_persistence(self):
        """
        Tests that the scene data is actually persisting in a saved blend file.
        https://github.com/EpicGames/BlenderTools/issues/491
        """
        self.run_scene_data_persistence_tests(
            file_name='temp_test.blend',
            property_data={
                'validate_textures': {
                    'non-default': True,
                    'default': False,
                },
                'export_custom_property_fcurves': {
                    'non-default': False,
                    'default': True,
                },
                'extensions.use_collections_as_folders.use_collections_as_folders': {
                    'non-default': True,
                    'default': False,
                },
                'extensions.combine_assets.combine': {
                    'non-default': 'child_meshes',
                    'default': 'off',
                }
            }
        )
