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

    @unittest.skip
    def test_use_object_origin_option(self):
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

    def test_animations(self):
        """
        Sends the mannequin animations to unreal with various options and ensures they are identical.
        """
        self.run_animation_tests({
            'SK_Mannequin_Female': {
                'rig': 'female_root',
                'animations': ['third_person_walk_01', 'third_person_run_01'],
                'bones': ['pelvis', 'calf_r', 'hand_l'],
                'frames': [1, 5, 14]
            }})

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

    def test_combine_child_meshes_option(self):
        """
        Tests the combine child mesh option.
        """
        self.blender.separate_mesh_by_selection('SK_Mannequin_Female', 'Head')
        self.move_to_collection(['female_root', 'SK_Mannequin_Female', 'Head'], 'Export')
        self.run_combine_child_meshes_option_tests(
            {'SK_Mannequin_Female': ['Head']},
            setup_parents=False
        )

    def test_use_immediate_parent_collection_name_option(self):
        """
        Tests the use immediate parent collection name option.
        https://github.com/EpicGames/BlenderTools/issues/202
        """
        self.move_to_collection(['female_root', 'SK_Mannequin_Female'], 'Export')
        self.run_use_immediate_parent_collection_name_option_tests({
            'SK_Mannequin_Female': ['Export', 'ParentCollectionName']
        })

    def test_use_collections_as_folders_option(self):
        """
        Tests using collections as folders option.
        https://github.com/EpicGames/BlenderTools/issues/183
        """
        self.move_to_collection(['female_root', 'SK_Mannequin_Female'], 'Export')
        self.run_use_collections_as_folders_option_tests({
            'SK_Mannequin_Female': ['Export', 'SomeFolder', 'Another']
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
