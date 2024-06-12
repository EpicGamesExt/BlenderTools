import sys
from utils.base_test_case import BaseSend2ueTestCaseCore, BaseSend2ueTestCase, SkipSend2UeTests
from test_send2ue_mannequins import TestSend2UeMannequins


class TestSend2UeExtensionCreatePostImportAssetsForGroomBase(BaseSend2ueTestCaseCore, BaseSend2ueTestCase):
    def run_create_post_import_assets_for_groom_option_tests(self, meshes_and_hairs):
        self.log(f'Creating binding asset...')

        # NOTE: passing in particle system names here only works because all particle modifiers share the same name
        # as their associated particle systems in the .blend mannequin test file
        for mesh_name, particle_names in meshes_and_hairs.items():
            self.blender.set_particles_visible(mesh_name, particle_names)

        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.create_post_import_assets_for_groom.binding_asset',
            True
        )

        self.send2ue_operation()

        for mesh_name, hairs in meshes_and_hairs.items():
            for hair_name in hairs:
                self.assert_binding_asset(hair_name, mesh_name)

        self.tearDown()

        for mesh_name, particle_names in meshes_and_hairs.items():
            self.blender.set_particles_visible(mesh_name, particle_names)

        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.create_post_import_assets_for_groom.binding_asset',
            True
        )
        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.create_post_import_assets_for_groom.blueprint_with_groom',
            True
        )

        self.log(f'Creating blueprint asset with skeletal mesh and groom components...')

        self.send2ue_operation()

        for mesh_name, hairs in meshes_and_hairs.items():
            blueprint_asset_name = f'{mesh_name}_BP'
            # Todo there is currently a failure on linux
            self.assert_blueprint_asset(blueprint_asset_name)

            for hair_name in hairs:
                binding_asset_name = f'{hair_name}_{mesh_name}_Binding'
                self.assert_blueprint_with_groom(blueprint_asset_name, hair_name, binding_asset_name, mesh_name)


class TestSend2UeExtensionCreatePostImportAssetsForGroomMannequins(
    SkipSend2UeTests,
    TestSend2UeMannequins,
    TestSend2UeExtensionCreatePostImportAssetsForGroomBase
):
    def test_extension(self):
        """
        Checks that the create post import assets for groom extension loaded properly.
        """
        self.run_extension_tests({
            'default': {
                'create_post_import_assets_for_groom': {
                    'properties': {
                        'binding_asset': True,
                        'blueprint_with_groom': False
                    },
                    'tasks': [
                        'pre_validations',
                        'post_import'
                    ],
                    'draws': [
                        'draw_import'
                    ]
                }
            }
        })

    def test_create_post_import_assets_for_groom_option(self):
        """
        Runs several test cases with the create post import assets extension for groom on the mannequin meshes.
        """
        if sys.platform == 'linux':
            self.skipTest(reason='#TODO Skipping on linux')

        self.move_to_collection([
            'male_root',
            'SK_Mannequin_LOD1'
        ], 'Export')

        self.move_to_collection([
            'back_curves',
            'shoulder_curves',
            'back_sparse_curves'
        ], 'Export')

        self.run_create_post_import_assets_for_groom_option_tests(meshes_and_hairs={
            'SK_Mannequin_LOD1': [
                'back_curves',
                'shoulder_curves',
                'back_sparse_curves',
                'particle_hair_waist',
                'particle_hair_hand_r'
            ]
        })
