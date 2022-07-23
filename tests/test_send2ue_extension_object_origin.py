from utils.base_test_case import BaseSend2ueTestCaseCore, SkipSend2UeTests
from test_send2ue_cubes import TestSend2UeCubes
from test_send2ue_mannequins import TestSend2UeMannequins


class TestSend2UeExtensionObjectOriginBase(BaseSend2ueTestCaseCore):
    def run_use_object_origin_option_tests(self, mesh_object, armature_object=None, animation_name=None):
        # turn object origin off
        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.object_origin.use_object_origin',
            False
        )

        # Notice blender units are meters and unreal units are centimeters
        location = [1.0, 1.0, 1.0]

        if armature_object:
            self.move_to_collection([mesh_object, armature_object], 'Export')
            self.set_object_transforms(armature_object, location=location)
            self.blender.set_animation_location(armature_object, location)
        else:
            self.move_to_collection([mesh_object], 'Export')
            self.set_object_transforms(mesh_object, location=location)

        self.send2ue_operation()
        self.assert_use_object_origin_option(mesh_object, location)

        # turn object origin on
        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.object_origin.use_object_origin',
            True
        )
        self.send2ue_operation()
        self.assert_use_object_origin_option(mesh_object, [0.0, 0.0, 0.0])


# class TestSend2UeExtensionObjectOriginCubes(
#     SkipSend2UeTests,
#     TestSend2UeCubes,
#     TestSend2UeExtensionObjectOriginBase
# ):
#     """
#     Runs several test cases with the object origin extension on the cube meshes.
#     """
#     def test_use_object_origin_option(self):
#         """
#         Offsets Cube1_LOD0 and tests with the use_object_origin option on and off.
#         https://github.com/EpicGames/BlenderTools/issues/223
#         """
#         self.run_use_object_origin_option_tests(
#             object_name='Cube1',
#             mesh_type='static_mesh'
#         )
#
#     def test_extension(self):
#         """
#         Checks that the combine_meshes extension loaded properly.
#         """
#         self.run_extension_tests({
#             'default': {
#                 'object_origin': {
#                     'properties': {
#                         'use_object_origin': False,
#                     },
#                     'tasks': [
#                         'pre_mesh_export',
#                         'post_mesh_export',
#                         # 'pre_animation_export',
#                         # 'post_animation_export'
#                     ],
#                     'draws': [
#                         'draw_export'
#                     ]
#                 }
#             }
#         })


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
            armature_object='female_root'
        )
