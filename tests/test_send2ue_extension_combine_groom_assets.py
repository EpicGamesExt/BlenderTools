from utils.base_test_case import BaseSend2ueTestCaseCore, BaseSend2ueTestCase, SkipSend2UeTests
from test_send2ue_cubes import TestSend2UeCubes
from test_send2ue_mannequins import TestSend2UeMannequins


class TestSend2UeExtensionCombineGroomAssetsBase(BaseSend2ueTestCaseCore, BaseSend2ueTestCase):
    def run_combine_groom_assets_option_tests(self, parents_meshes_and_particles, combine_option):
        self.log(f'>>> Testing for the combine groom option: "{combine_option}"...')

        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.create_binding_asset.create_binding_asset',
            True
        )

        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.combine_meshes.combine_child_meshes',
            False
        )

        self.send2ue_operation()

        if combine_option == 'off':
            for meshes in parents_meshes_and_particles.values():
                for mesh, particle_systems in meshes.items():
                    curves, hair, emitter = self.get_particles_by_type(particle_systems)
                    for particle in hair + curves:
                        self.assert_groom_import(particle, True)
                        self.assert_binding_asset(particle, mesh)
                    for particle in emitter:
                        self.assert_groom_import(particle, False)

        elif combine_option == 'combine_groom_for_each_mesh':
            for meshes in parents_meshes_and_particles.values():
                for mesh, particle_systems in meshes.items():
                    curves, hair, emitter = self.get_particles_by_type(particle_systems)
                    if len(hair + curves) > 0:
                        if len(hair) > 0:
                            self.assert_groom_import(hair[0], True)
                            self.assert_binding_asset(hair[0], mesh)

                            particles = hair + curves + emitter
                            for particle in particles[1:]:
                                self.assert_groom_import(particle, False)
                        else:
                            self.assert_groom_import(curves[0], True)
                            self.assert_binding_asset(curves[0], mesh)

                            particles = curves + emitter
                            for particle in particles[1:]:
                                self.assert_groom_import(particle, False)

        elif combine_option == 'combine_all_groom':
            self.assert_groom_import('combined_groom', True)
            for meshes in parents_meshes_and_particles.values():
                for particle_systems in meshes.values():
                    curves, hair, emitter = self.get_particles_by_type(particle_systems)
                    for particle in curves + hair + emitter:
                        self.assert_groom_import(particle, False)

        self.tearDown()

        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.create_binding_asset.create_binding_asset',
            True
        )

        self.log(f'### Turning on combine meshes extension...')

        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.combine_meshes.combine_child_meshes',
            True
        )

        self.send2ue_operation()

        if combine_option == 'off':
            for meshes_and_particles in parents_meshes_and_particles.values():
                meshes = meshes_and_particles.keys()
                if len(meshes) > 0:
                    head_mesh = list(meshes)[0]
                    for particle_systems in meshes_and_particles.values():
                        curves, hair, emitter = self.get_particles_by_type(particle_systems)
                        for particle in hair + curves:
                            self.assert_groom_import(particle, True)
                            self.assert_binding_asset(particle, head_mesh)
                        for particle in emitter:
                            self.assert_groom_import(particle, False)

        elif combine_option == 'combine_groom_for_each_mesh':
            for meshes_and_particles in parents_meshes_and_particles.values():
                meshes = meshes_and_particles.keys()
                if len(meshes) > 0:
                    head_mesh = list(meshes)[0]
                    groom_asset_name = head_mesh + '_groom'
                    self.assert_groom_import(groom_asset_name, True)
                    self.assert_binding_asset(groom_asset_name, head_mesh)
                    for particle_systems in meshes_and_particles.values():
                        curves, hair, emitter = self.get_particles_by_type(particle_systems)
                        for particle in curves + hair + emitter:
                            self.assert_groom_import(particle, False)

        elif combine_option == 'combine_all_groom':
            self.assert_groom_import('combined_groom', True)
            for meshes in parents_meshes_and_particles.values():
                for particle_systems in meshes.values():
                    curves, hair, emitter = self.get_particles_by_type(particle_systems)
                    for particle in curves + hair + emitter:
                        self.assert_groom_import(particle, False)

        self.tearDown()

    def get_particles_by_type(self, particle_systems):
        curves = particle_systems.get('curves')
        particle_hair = particle_systems.get('particle_hair')
        particle_emitter = particle_systems.get('particle_emitter')
        return curves, particle_hair, particle_emitter

    def set_combine_groom_option(self, option):
        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.combine_groom_assets.combine_groom_assets',
            option)


class TestSend2UeExtensionCombineGroomAssetsMannequins(
    SkipSend2UeTests,
    TestSend2UeMannequins,
    TestSend2UeExtensionCombineGroomAssetsBase
):
    def test_extension(self):
        """
        Checks that the combine groom assets extension loaded properly.
        """
        self.run_extension_tests({
            'default': {
                'combine_groom_assets': {
                    'properties': {
                        'combine_groom_assets': 'off'
                    },
                    'tasks': [
                        'pre_operation',
                        'filter_objects',
                        'pre_groom_export',
                        'post_groom_export',
                        'post_import'
                    ],
                    'draws': [
                        'draw_export'
                    ]
                }
            }
        })

    """
    Runs several test cases with the use immediate parent name extension on the mannequin meshes.
    """
    def test_combine_groom_assets_option(self):
        """
        """
        self.move_to_collection([
            'male_root',
            'SK_Mannequin_LOD0',
            'SK_Mannequin_LOD1',
            'SK_Mannequin_LOD2',
            'SK_Mannequin_LOD3'
        ], 'Export')

        self.move_to_collection([
            'male_root_no_groom',
            'SK_NG_Mannequin_LOD0',
            'SK_NG_Mannequin_LOD1',
            'SK_NG_Mannequin_LOD2',
            'SK_NG_Mannequin_LOD3'
        ], 'Export')

        self.move_to_collection([
            'female_root',
            'SK_Mannequin_Female'
        ], 'Export')

        self.move_to_collection([
            'back_curves',
            'shoulder_curves'
        ], 'Export')

        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.combine_meshes.combine_child_meshes',
            False
        )

        combine_groom_options = ['off', 'combine_groom_for_each_mesh', 'combine_all_groom']
        for option in combine_groom_options:
            self.set_combine_groom_option(option)
            self.run_combine_groom_assets_option_tests(parents_meshes_and_particles={
                'male_root': {
                    'SK_Mannequin_LOD0': {
                        'curves': [],
                        'particle_hair': [],
                        'particle_emitter': [],
                    },
                    'SK_Mannequin_LOD1': {
                        'curves': ['back_curves', 'shoulder_curves'],
                        'particle_hair': ['particle_hair_waist', 'particle_hair_hand_r'],
                        'particle_emitter': ['particle_emitter'],
                    },
                    'SK_Mannequin_LOD2': {
                        'curves': [],
                        'particle_hair': ['particle_hair_hand_l'],
                        'particle_emitter': ['particle_emitter2'],
                    },
                    'SK_Mannequin_LOD3': {
                        'curves': [],
                        'particle_hair': [],
                        'particle_emitter': ['particle_emitter3'],
                    }
                },
                'female_root': {
                    'SK_Mannequin_Female': {
                        'curves': [],
                        'particle_hair': ['particle_hair_head'],
                        'particle_emitter': [],
                    }
                }
            },
                combine_option=option
            )

    def test_animations(self):
        """
        Sends the mannequin animations to unreal with various options and ensures they are identical.
        """
        # disable the auto remove option so the tests get the right animations
        self.blender.set_addon_property('scene', 'send2ue', 'auto_remove_original_asset_names', False)

        self.run_animation_tests({
            'SK_Mannequin_Female': {
                'rig': 'female_root',
                'animations': ['third_person_run_01', 'third_person_walk_01'],
                'bones': ['pelvis', 'calf_r', 'hand_l'],
                'frames': [1, 5, 14]
            }})
