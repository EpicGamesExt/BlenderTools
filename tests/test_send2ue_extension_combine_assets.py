from utils.base_test_case import BaseSend2ueTestCaseCore, BaseSend2ueTestCase, SkipSend2UeTests
from test_send2ue_cubes import TestSend2UeCubes
from test_send2ue_mannequins import TestSend2UeMannequins


class TestSend2UeExtensionCombineAssetsBase(BaseSend2ueTestCaseCore, BaseSend2ueTestCase):
    def run_meshes_tests(self, parent_name, meshes_and_particles, combine_option, mesh_type):
        child_meshes = list(meshes_and_particles.keys())
        if child_meshes:
            head_mesh_name = child_meshes[0]
            if combine_option in ['off', 'groom_per_mesh']:
                for mesh in child_meshes:
                    self.assert_mesh_import(mesh, True)
            else:
                if mesh_type == 'StaticMesh':
                    self.assert_mesh_import(parent_name, True)
                elif mesh_type == 'SkeletalMesh':
                    self.assert_mesh_import(head_mesh_name, True)
                    child_meshes.remove(head_mesh_name)
                for mesh in child_meshes:
                    self.assert_mesh_import(mesh, False)

            if mesh_type == 'StaticMesh':
                return parent_name
            return head_mesh_name
        else:
            return None

    def run_binding_assets_tests(self, groom_asset_name, target_mesh_name, mesh_type):
        if mesh_type == 'SkeletalMesh':
            self.assert_binding_asset(groom_asset_name, target_mesh_name)

    def run_combine_assets_option_tests(self, parents_meshes_and_particles, combine_option, mesh_type):
        self.log(f'Testing for the combine assets option: "{combine_option}"...')

        for meshes_and_particles in parents_meshes_and_particles.values():
            for mesh_name, particle_names in meshes_and_particles.items():
                curves, hair, emitter, disabled = self.get_particles_by_type(particle_names)

                all_particle_names = {
                    'enabled': hair + emitter,
                    'disabled': disabled
                }

                # NOTE: passing in particle system names here only works because all particle modifiers share the
                # same name as their associated particle systems in the .blend mannequin test file
                self.set_select_particles_visible(mesh_name, all_particle_names)

        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.create_post_import_assets_for_groom.binding_asset',
            True
        )

        self.send2ue_operation()

        for parent, meshes_and_particles in parents_meshes_and_particles.items():
            head_mesh = self.run_meshes_tests(parent, meshes_and_particles, combine_option, mesh_type)

            if combine_option == 'off':
                for mesh, particle_systems in meshes_and_particles.items():
                    curves, hair, emitter, disabled = self.get_particles_by_type(particle_systems)
                    for particle in hair + curves:
                        self.assert_groom_import(particle, True)
                        self.run_binding_assets_tests(particle, mesh, mesh_type)
                    for particle in emitter:
                        self.assert_groom_import(particle, False)

            elif combine_option == 'groom_per_mesh':
                for mesh, particle_systems in meshes_and_particles.items():
                    curves, hair_names, emitter, disabled = self.get_particles_by_type(particle_systems)
                    # only check if there are hair particles or curves on the object
                    if curves + hair_names:
                        combined_groom_name = f'{mesh}_Groom'
                        self.assert_groom_import(combined_groom_name, True)
                        self.run_binding_assets_tests(combined_groom_name, mesh, mesh_type)

                    # check that these dont exist
                    for particle_name in hair_names + curves + emitter + disabled:
                        self.assert_groom_import(particle_name, False)

            elif combine_option == 'child_meshes':
                if head_mesh:
                    for particle_systems in meshes_and_particles.values():
                        curves, hair, emitter, disabled = self.get_particles_by_type(particle_systems)
                        for particle in hair + curves:
                            self.assert_groom_import(particle, True)
                            self.run_binding_assets_tests(particle, head_mesh, mesh_type)
                        for particle in emitter + disabled:
                            self.assert_groom_import(particle, False)

            elif combine_option == 'groom_per_combined_mesh':
                if head_mesh:
                    for particle_systems in meshes_and_particles.values():
                        curves, hair, emitter, disabled = self.get_particles_by_type(particle_systems)
                        if curves + hair:
                            groom_asset_name = f'{head_mesh}_Groom'
                            self.assert_groom_import(groom_asset_name, True)
                            self.run_binding_assets_tests(groom_asset_name, head_mesh, mesh_type)
                            for particle in curves + hair + emitter + disabled:
                                self.assert_groom_import(particle, False)

        self.tearDown()

    def get_particles_by_type(self, particle_systems):
        curves = particle_systems.get('curves')
        particle_hair = particle_systems.get('particle_hair')
        particle_emitter = particle_systems.get('particle_emitter')
        disabled = particle_systems.get('disabled')

        return curves, particle_hair, particle_emitter, disabled

    def set_combine_option(self, option):
        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.combine_assets.combine',
            option)

    def setup_parents(self, children, parent_name, mesh_type='StaticMesh'):
        if mesh_type == 'StaticMesh':
            self.blender.create_empty(parent_name)
            for offset, child_name in enumerate(children, 1):
                self.set_object_transforms(child_name, location=[0.0, offset * 2, 0.0])
                self.log(f'Parenting "{child_name}" to "{parent_name}"...')
                self.blender.parent_to(child_name, parent_name)

        # TODO: separation is not used currently
        elif mesh_type == 'SkeletalMesh':
            self.blender.separate_mesh_by_selection(children[0], children[-1])


class TestSend2UeExtensionCombineAssetsCubes(
    SkipSend2UeTests,
    TestSend2UeCubes,
    TestSend2UeExtensionCombineAssetsBase
):
    def test_combine_assets_option(self):
        """
        Runs several test cases with the combine assets extension on the cube meshes.
        """
        cubes = [
            'Cube1_LOD0',
            'Cube1_LOD1',
            'Cube1_LOD2',
        ]
        self.setup_parents(cubes, 'CombinedCubes')

        self.move_to_collection(cubes + ['CombinedCubes'], 'Export')

        self.move_to_collection([
            'Cube1_hair_curves',
        ], 'Export')

        combine_options = [
            'off',
            'child_meshes',
            'groom_per_mesh',
            'groom_per_combined_mesh'
        ]

        for option in combine_options:
            self.set_combine_option(option)
            self.run_combine_assets_option_tests(parents_meshes_and_particles={
                'CombinedCubes': {
                    'Cube1_LOD0': {
                        'curves': [],
                        'particle_hair': [],
                        'particle_emitter': [],
                        'disabled': []
                    },
                    'Cube1_LOD1': {
                        'curves': [],
                        'particle_hair': ['cube_particle_hair'],
                        'particle_emitter': ['cube_particle_emitter'],
                        'disabled': []
                    },
                    'Cube1_LOD2': {
                        'curves': ['Cube1_hair_curves'],
                        'particle_hair': [],
                        'particle_emitter': [],
                        'disabled': []
                    }
                }
            },
                combine_option=option,
                mesh_type='StaticMesh'
            )


class TestSend2UeExtensionCombineAssetsMannequins(
    SkipSend2UeTests,
    TestSend2UeMannequins,
    TestSend2UeExtensionCombineAssetsBase
):
    def test_extension(self):
        """
        Checks that the combine groom assets extension loaded properly.
        """
        self.run_extension_tests({
            'default': {
                'combine_assets': {
                    'properties': {
                        'combine': 'off'
                    },
                    'tasks': [
                        'pre_operation',
                        'filter_objects',
                        'pre_mesh_export',
                        'pre_groom_export'
                    ],
                    'draws': [
                        'draw_export'
                    ]
                }
            }
        })

    def test_combine_assets_option(self):
        """
        Runs several test cases with the combine assets extension on the mannequin meshes.
        """
        self.move_to_collection([
            'male_root',
            'SK_Mannequin_LOD0',
            'SK_Mannequin_LOD1',
            'SK_Mannequin_LOD2',
            'SK_Mannequin_LOD3'
        ], 'Export')

        self.move_to_collection([
            'female_root',
            'SK_Mannequin_Female'
        ], 'Export')

        self.move_to_collection([
            'back_curves',
            'shoulder_curves',
            'back_sparse_curves'
        ], 'Export')

        combine_options = [
            'off',
            'child_meshes',
            'groom_per_mesh',
            'groom_per_combined_mesh',
        ]

        for option in combine_options:
            self.set_combine_option(option)
            self.run_combine_assets_option_tests(parents_meshes_and_particles={
                'male_root': {
                    'SK_Mannequin_LOD0': {
                        'curves': [],
                        'particle_hair': [],
                        'particle_emitter': [],
                        'disabled': ['particle_hair_disabled']
                    },
                    'SK_Mannequin_LOD1': {
                        'curves': ['back_curves', 'shoulder_curves', 'back_sparse_curves'],
                        'particle_hair': ['particle_hair_waist', 'particle_hair_hand_r'],
                        'particle_emitter': ['particle_emitter'],
                        'disabled': []
                    },
                    'SK_Mannequin_LOD2': {
                        'curves': [],
                        'particle_hair': ['particle_hair_hand_l'],
                        'particle_emitter': ['particle_emitter2'],
                        'disabled': []
                    },
                    'SK_Mannequin_LOD3': {
                        'curves': [],
                        'particle_hair': [],
                        'particle_emitter': ['particle_emitter3'],
                        'disabled': []
                    }
                },
                'female_root': {
                    'SK_Mannequin_Female': {
                        'curves': [],
                        'particle_hair': ['particle_hair_head'],
                        'particle_emitter': [],
                        'disabled': []
                    }
                }
            },
                combine_option=option,
                mesh_type='SkeletalMesh'
            )
