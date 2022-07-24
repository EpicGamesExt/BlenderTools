from utils.base_test_case import BaseSend2ueTestCaseCore, BaseSend2ueTestCase, SkipSend2UeTests
from test_send2ue_cubes import TestSend2UeCubes
from test_send2ue_mannequins import TestSend2UeMannequins


class TestSend2UeExtensionObjectOriginBase(BaseSend2ueTestCaseCore, BaseSend2ueTestCase):
    def run_use_object_origin_option_tests(
        self,
        mesh_object,
        armature_object=None,
        animation_name=None,
        bone_name=None,
        frame=None
    ):
        # turn object origin off
        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.object_origin.use_object_origin',
            False
        )

        # Notice blender units are meters and unreal units are centimeters
        # The offset is 15cm since bone floating point precision starts to break down at larger offsets
        # and the assertions the test cases make on the animation would not match exactly
        location = [0.15, 0.15, 0.15]

        if armature_object:
            self.move_to_collection([mesh_object, armature_object], 'Export')
            self.set_object_transforms(armature_object, location=location)
            self.blender.set_all_action_locations(location)
            self.blender.set_addon_property('scene', 'send2ue', 'import_animations', True)
        else:
            self.move_to_collection([mesh_object], 'Export')
            self.set_object_transforms(mesh_object, location=location)

        self.send2ue_operation()

        if armature_object:
            self.assert_animation_translation(armature_object, animation_name, bone_name, frame)
        else:
            self.assert_mesh_origin(mesh_object, location)

        # turn object origin on
        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.object_origin.use_object_origin',
            True
        )

        location = [0.0, 0.0, 0.0]
        self.send2ue_operation()
        if armature_object:
            self.assert_animation_translation(armature_object, animation_name, bone_name, frame)
        else:
            self.assert_mesh_origin(mesh_object, location)


class TestSend2UeExtensionObjectOriginCubes(
    SkipSend2UeTests,
    TestSend2UeCubes,
    TestSend2UeExtensionObjectOriginBase
):
    """
    Runs several test cases with the object origin extension on the cube meshes.
    """
    def test_use_object_origin_option(self):
        """
        Offsets Cube1_LOD0 and tests with the use_object_origin option on and off.
        https://github.com/EpicGames/BlenderTools/issues/223
        """
        self.run_use_object_origin_option_tests(
            mesh_object='Cube1'
        )

    def test_extension(self):
        """
        Checks that the combine_meshes extension loaded properly.
        """
        self.run_extension_tests({
            'default': {
                'object_origin': {
                    'properties': {
                        'use_object_origin': False,
                    },
                    'tasks': [
                        'pre_mesh_export',
                        'post_mesh_export',
                        'pre_animation_export',
                        'post_animation_export'
                    ],
                    'draws': [
                        'draw_export'
                    ]
                }
            }
        })


class TestSend2UeExtensionObjectOriginMannequins(
    SkipSend2UeTests,
    TestSend2UeMannequins,
    TestSend2UeExtensionObjectOriginBase
):
    """
    Runs several test cases with the object origin extension on the mannequin meshes.
    """
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
