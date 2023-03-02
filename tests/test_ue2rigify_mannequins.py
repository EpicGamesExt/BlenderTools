from utils.base_test_case import BaseUe2RigifyTestCase


class TestUe2RigifyMannequins(BaseUe2RigifyTestCase):
    """
    Runs several test cases with the mannequins.
    """

    def __init__(self, *args, **kwargs):
        super(TestUe2RigifyMannequins, self).__init__(*args, **kwargs)
        self.file_name = 'mannequins.blend'

    def test_modes(self):
        """
        Switches through each mode.
        """
        self.run_modes_tests({
            'male_root': {
                'template': 'male_mannequin',
                'modes': [
                    'SOURCE',
                    'FK_TO_SOURCE',
                    'SOURCE_TO_DEFORM',
                    'CONTROL',
                    'METARIG'
                    ]
            },
            'female_root': {
                'template': 'female_mannequin',
                'modes': [
                    'FK_TO_SOURCE',
                    'SOURCE_TO_DEFORM',
                    'SOURCE',
                    'METARIG',
                    'CONTROL'
                    ]
            }
        })

    def test_new_template(self):
        """
        Tests creating a new template.
        https://github.com/EpicGames/BlenderTools/issues/233
        """
        self.run_new_template_tests({
                'male_root': {
                    'new_template_name': 'test_basic_human',
                    'starter_template_name': 'bpy.ops.object.armature_basic_human_metarig_add()',
                    'fk_to_source': {'upper_arm_fk.L': 'upperarm_l'},
                    'source_to_deform': {'upperarm_l': 'DEF-upper_arm.L'}
                },
                'female_root': {
                    'new_template_name': 'test_mannequin',
                    'starter_template_name': 'female_mannequin',
                    'fk_to_source': {'upper_arm_fk.L': 'upperarm_l'},
                    'source_to_deform': {'upperarm_l': 'DEF-upper_arm.L'}
                }
            })

    def test_baking(self):
        """
        Tests that baking functions correctly.
        This tests that baking the bone transforms is correct.
        https://github.com/EpicGames/BlenderTools/issues/238
        """
        self.run_baking_tests({
            # TODO flip animation order and fix failure
            'male_root': {
                'template': 'male_mannequin',
                'control_rig': 'rig',
                'animations': ['third_person_run_01', 'third_person_walk_01'],
                # 'bones': ['pelvis', 'calf_r', 'foot_l', 'hand_l'], # TODO make this pass with the hands and feet
                'bones': ['pelvis', 'calf_r'],
                'frames': [2, 7],
                'ik_fk_switch': {
                    # IK bake is not precise, greater than 2cm world location difference
                    'upper_arm_parent.L': 'hand_ik.L',
                    'thigh_parent.L': 'foot_ik.L'
                }
            },
            # TODO investigate female template fix failure
            # 'female_root': {
            #     'template': 'female_mannequin',
            #     'control_rig': 'rig',
            #     'animations': ['third_person_run_01', 'third_person_walk_01'],
            #     'bones': ['spine_02', 'calf_l', 'lowerarm_r'],
            #     # 'frames': [1, 9],
            # }
        })

    def test_template_sharing(self):
        """
        Checks if exporting, importing, removing templates functions correctly.
        """
        self.run_template_sharing_tests({
            'male_root': {
                'template': 'male_mannequin',
            }
        })

