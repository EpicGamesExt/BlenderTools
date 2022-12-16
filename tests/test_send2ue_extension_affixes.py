import unittest
from utils.base_test_case import BaseSend2ueTestCaseCore, SkipSend2UeTests
from test_send2ue_cubes import TestSend2UeCubes
from test_send2ue_mannequins import TestSend2UeMannequins


def setUp(self):
    """
    The setup for affix test cases.
    """
    self.blender.set_addon_property('scene', 'send2ue', 'extensions.affixes.auto_add_asset_name_affixes', True)
    self.blender.set_addon_property('scene', 'send2ue', 'extensions.affixes.auto_remove_asset_name_affixes', False)


class TestSend2UeExtensionAffixesCubes(SkipSend2UeTests, TestSend2UeCubes, BaseSend2ueTestCaseCore):
    """
    Runs several test cases with the affix extension on the cube meshes.
    """
    def setUp(self):
        super().setUp()
        setUp(self)

    def test_extension(self):
        """
        Checks that the affix extension loaded properly.
        """
        self.run_extension_tests({
            'default': {
                'affixes': {
                    'properties': {
                        'auto_add_asset_name_affixes': True,
                        'auto_remove_asset_name_affixes': False,
                        'static_mesh_name_affix': 'SM_',
                        'material_name_affix': 'M_',
                        'texture_name_affix': 'T_',
                        'skeletal_mesh_name_affix': 'SK_',
                        'animation_sequence_name_affix': 'Anim_',
                    },
                    'tasks': [
                        'post_operation',
                        'pre_operation',
                        'pre_validations'
                    ],
                    'utility_operators': [
                        'extensions_affixes_addassetaffixes',
                        'extensions_affixes_removeassetaffixes'
                    ],
                    'draws': [
                        'draw_export'
                    ]
                }
            }
        })

    def test_default_send_to_unreal(self):
        """
        Sends a cube mesh with default settings.
        """
        self.move_to_collection(['Cube1_LOD0'], 'Export')
        self.send2ue_operation()
        self.assert_mesh_import('SM_Cube1_LOD0')

    def test_materials(self):
        """
        Sends a Cube with materials to unreal.
        """
        self.run_material_tests({
            'Cube1_LOD0': {
                'asset': 'SM_Cube1_LOD0',
                'materials': {
                    'M_Material': 0,
                    'M_blue': 1,
                    'M_red': 2,
                    'M_green': 3,
                }
            },
            'Cube2_lod0_mesh': {
                'asset': 'SM_Cube2_lod0_mesh',
                'materials': {
                    'M_unreal': 0,
                    'M_Material': 1
                }
            },
        })

    def test_textures(self):
        """
        Sends a Cube with a textured material to unreal.
        https://github.com/EpicGames/BlenderTools/issues/83
        """
        self.run_texture_tests({
            'Cube2_lod0_mesh': ['T_unreal-engine-logo'],
        })


class TestSend2UeExtensionAffixesMannequins(SkipSend2UeTests, TestSend2UeMannequins):
    """
    Runs several test cases with the affix extension on the mannequin meshes.
    """
    def setUp(self):
        super().setUp()
        setUp(self)

    def test_default_send_to_unreal(self):
        """
        Sends a mannequin mesh with default settings.
        """
        self.move_to_collection(['female_root', 'SK_Mannequin_Female'], 'Export')
        self.send2ue_operation()
        self.assert_mesh_import('SK_Mannequin_Female')
        self.run_skeleton_tests('SK_Mannequin_Female')

    def test_animations(self):
        """
        Sends the mannequin animations to unreal with various options and ensures they are identical.
        """
        # disable the auto remove option so the tests get the right animations
        self.blender.set_addon_property('scene', 'send2ue', 'auto_remove_original_asset_names', False)

        self.run_animation_tests({
            'SK_Mannequin_Female': {
                'rig': 'female_root',
                # 'animations': ['Anim_third_person_walk_01', 'Anim_third_person_run_01'],
                'animations': ['Anim_third_person_run_01'],
                'bones': ['pelvis', 'calf_r', 'hand_l'],
                'frames': [1, 5, 14],
                'grooms': ['particle_hair_head']
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
                    'M_MI_Female_Body': 0,
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
            'SK_Mannequin_Female': ['T_unreal-engine-logo'],
        })
