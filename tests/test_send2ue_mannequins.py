import unittest
from utils.base_test_case import BaseSend2ueTestCase


class TestSend2UeMannequins(BaseSend2ueTestCase):
    """
    Runs several test cases with the mannequin meshes.
    """

    def __init__(self, *args, **kwargs):
        super(TestSend2UeMannequins, self).__init__(*args, **kwargs)
        self.file_name = 'mannequins.blend'

    @unittest.skip
    def test_sockets(self):
        pass

    @unittest.skip
    def test_collisions(self):
        pass

    def test_default_send_to_unreal(self):
        """
        Sends a mannequin mesh with default settings.
        """
        self.move_to_collection(['female_root', 'SK_Mannequin_Female'], 'Export')
        self.send2ue_operation()
        self.assert_mesh_import('SK_Mannequin_Female')
        self.run_skeleton_tests('SK_Mannequin_Female')

    def test_bulk_send_to_unreal(self):
        """
        Sends multiple mannequins to unreal at once.
        """
        self.move_to_collection(['male_root', 'SK_Mannequin_LOD0'], 'Export')
        self.move_to_collection(['female_root', 'SK_Mannequin_Female'], 'Export')
        self.send2ue_operation()
        self.assert_mesh_import('SK_Mannequin_Female')
        self.assert_mesh_import('SK_Mannequin_LOD0')

        self.tearDown()

        animation_names = ['third_person_walk_01', 'third_person_run_01']
        groom_names = ['particle_hair_head']

        self.blender.set_addon_property('scene', 'send2ue', 'import_meshes', True)
        self.blender.set_addon_property('scene', 'send2ue', 'import_animations', False)
        self.blender.set_addon_property('scene', 'send2ue', 'import_grooms', False)

        for animation in animation_names:
            self.assert_animation_import(animation, False)
        for groom_name in groom_names:
            self.assert_groom_import(groom_name, False)

    def test_lods(self):
        """
        Sends a mannequin mesh with lods to unreal.
        """
        lods = ['SK_Mannequin_LOD0', 'SK_Mannequin_LOD1', 'SK_Mannequin_LOD2', 'SK_Mannequin_LOD3']
        self.move_to_collection(['male_root'], 'Export')
        lod_build_settings = {
            'recompute_normals': True,
            'recompute_tangents': True,
            'use_mikk_t_space': True,
            'remove_degenerates': True
        }
        self.run_lod_tests('SK_Mannequin', lods, lod_build_settings, 'skeletal')

        self.log('testing re-importing lods...')
        self.run_lod_tests('SK_Mannequin', lods, lod_build_settings, 'skeletal')

    def test_animations(self):
        """
        Sends the mannequin animations to unreal with various options and ensures they are identical.
        """
        self.run_animation_tests({
            'SK_Mannequin_Female': {
                'rig': 'female_root',
                'animations': ['third_person_walk_01', 'third_person_run_01'],
                'bones': ['pelvis', 'calf_r', 'hand_l'],
                'frames': [1, 5, 14],
                'grooms': ['particle_hair_head']
            }})

    def test_grooms(self):
        """
        Sends a mannequin with curves and hair particles to unreal.
        """

        sk_mannequin_meshes = [
            'SK_Mannequin_LOD0',
            'SK_Mannequin_LOD1',
            'SK_Mannequin_LOD2',
            'SK_Mannequin_LOD3'
        ]

        sk_mannequin_female_meshes = ['SK_Mannequin_Female']

        self.move_to_collection(
            ['male_root'] + sk_mannequin_meshes,
            'Export')

        self.move_to_collection(
            ['female_root'] + sk_mannequin_female_meshes,
            'Export')

        self.move_to_collection([
            'back_curves',
            'shoulder_curves',
            'back_sparse_curves'
        ], 'Export')

        self.run_groom_tests({
            'SK_Mannequin_LOD1': {
                'curves': ['back_curves', 'shoulder_curves', 'back_sparse_curves'],
                'particle_hair': ['particle_hair_waist', 'particle_hair_hand_r'],
                'particle_emitter': ['particle_emitter'],
                'disabled': ['particle_hair_disabled']
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
            },
            'SK_Mannequin_Female': {
                'curves': [],
                'particle_hair': ['particle_hair_head'],
                'particle_emitter': [],
                'disabled': []
            }
        })

        self.tearDown()

        animation_names = ['third_person_walk_01', 'third_person_run_01']
        mesh_names = sk_mannequin_meshes + sk_mannequin_female_meshes

        self.blender.set_addon_property('scene', 'send2ue', 'import_meshes', False)
        self.blender.set_addon_property('scene', 'send2ue', 'import_animations', False)
        self.blender.set_addon_property('scene', 'send2ue', 'import_grooms', True)

        for animation_name in animation_names:
            self.assert_animation_import(animation_name, False)
        for mesh_name in mesh_names:
            self.assert_mesh_import(mesh_name, False)

        self.tearDown()

    def test_materials(self):
        """
        Sends a mannequin with materials to unreal.
        """
        self.move_to_collection(['female_root'], 'Export')
        self.run_material_tests({
            'SK_Mannequin_Female': {
                'asset': 'SK_Mannequin_Female',
                'materials': {
                    'MI_Female_Body': 0,
                    'M_UE4Man_ChestLogo': 1
                }
            }
        })

    def test_textures(self):
        """
        Sends a mannequin with a textured material to unreal.
        """
        self.move_to_collection(['female_root'], 'Export')
        self.run_texture_tests({
            'SK_Mannequin_Female': ['unreal-engine-logo'],
        })

    def test_auto_stash_active_action_option(self):
        """
        Tests not using auto stash active action option.
        """
        self.run_auto_stash_active_action_option_tests({
            'SK_Mannequin_Female': {
                'rig': 'female_root',
                'animations': ['third_person_walk_01', 'third_person_run_01']
            }})

    def test_export_object_name_as_root_option(self):
        """
        Tests export object name as root option.
        """
        self.run_export_object_name_as_root_option_tests({
            'SK_Mannequin_Female': {
                'rig': 'female_root',
                'animations': ['third_person_walk_01', 'third_person_run_01'],
                'bones': ['spine_02', 'calf_l', 'lowerarm_r'],
                'frames': [2, 6, 11]
            }})

    def test_export_custom_property_fcurves_option(self):
        """
        Tests export custom property fcurves option.
        """
        self.run_export_custom_property_fcurves_option_tests({
            'SK_Mannequin_Female': {
                'rig': 'female_root',
                'animations': {
                    'third_person_walk_01': {'head_swell': True},
                    'third_person_run_01': {'head_swell': False}
                }
            }})

    def test_use_object_origin_option(self):
        """
        Offsets SK_Female_Mannequin and tests with the use_object_origin option on and off.
        """
        self.run_use_object_origin_option_tests(
            mesh_object='SK_Mannequin_Female',
            armature_object='female_root',
            animation_name='third_person_walk_01',
            bone_name='pelvis',
            frame=1
        )
