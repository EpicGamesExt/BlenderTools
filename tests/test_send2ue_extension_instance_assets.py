import re
from utils.base_test_case import BaseSend2ueTestCaseCore, SkipSend2UeTests, BaseSend2ueTestCase
from test_send2ue_cubes import TestSend2UeCubes
from test_send2ue_mannequins import TestSend2UeMannequins


class TestSend2UeExtensionInstanceAssetsBase(
    SkipSend2UeTests,
    BaseSend2ueTestCaseCore,
    BaseSend2ueTestCase
):

    def run_instance_asset_tests(
        self,
        mesh_object,
        location_offset,
        armature_object=None,
        animation_name=None
    ):
        # turn place in active level off
        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.instance_assets.place_in_active_level',
            False
        )

        if armature_object:
            self.move_to_collection([mesh_object, armature_object], 'Export')
            self.set_object_transforms(armature_object, location=location_offset)
            self.blender.set_all_action_locations(location_offset)
            self.blender.set_addon_property('scene', 'send2ue', 'import_animations', True)
        else:
            self.move_to_collection([mesh_object], 'Export')
            self.set_object_transforms(mesh_object, location=location_offset)

        self.send2ue_operation()

        # check that the assets were not spawned in the level
        self.assert_actor_location(mesh_object, location_offset, exists=False)
        if animation_name:
            self.assert_actor_location(animation_name, location_offset, exists=False)
        else:
            self.assert_actor_location(mesh_object, location_offset, exists=False)

        # make sure that the import area is clean so assets don't overwrite each other
        self.tearDown()

        # turn place in active level on
        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.instance_assets.place_in_active_level',
            True
        )

        self.send2ue_operation()

        # check that the assets were spawned in the level with the correct transforms
        self.assert_actor_location(mesh_object, location_offset, exists=True)
        if animation_name:
            self.assert_actor_location(animation_name, location_offset, exists=True)
        else:
            self.assert_actor_location(mesh_object, location_offset, exists=True)

    def run_use_mesh_instances_tests(
        self,
        mesh_object,
        location_offset
    ):
        # turn place in active level on
        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.instance_assets.place_in_active_level',
            True
        )
        # turn use mesh instances on
        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.instance_assets.use_mesh_instances',
            True
        )

        # sets the location of the mesh object
        self.set_object_transforms(mesh_object, location=location_offset)

        # duplicate the mesh object with linked mesh data
        duplicate_object_name = f'{mesh_object}_duplicated'
        duplicate_object_location = [i + 1 for i in location_offset]
        mesh_data_name = self.blender.duplicate_with_linked_data(
            mesh_object,
            duplicate_object_name,
            duplicate_object_location
        )
        # make sure we get the valid unreal name
        instanced_mesh_asset_name = re.sub(
            self.send2ue.constants.RegexPresets.INVALID_NAME_CHARACTERS,
            "_",
            mesh_data_name.strip()
        )

        # move both meshes to export collection
        self.move_to_collection([mesh_object, duplicate_object_name], 'Export')
        self.send2ue_operation()

        # ensure only an object with the mesh data instance name is imported and not an asset per object name
        self.assert_mesh_import(instanced_mesh_asset_name, exists=True)
        self.assert_mesh_import(mesh_object, exists=False)
        self.assert_mesh_import(duplicate_object_name, exists=False)

        # check that actors are created that match the object names
        self.assert_actor_location(mesh_object, location_offset, exists=True)
        self.assert_actor_location(duplicate_object_name, duplicate_object_location, exists=True)


class TestSend2UeExtensionInstanceAssetsCubes(
    TestSend2UeExtensionInstanceAssetsBase,
    TestSend2UeCubes
):
    """
    Runs several test cases with the instance assets extension on the cube meshes.
    """

    def test_place_in_active_level_option(self):
        """
        Tests using place in active level option.
        """
        self.run_instance_asset_tests(
            mesh_object='Cube1',
            location_offset=[1.0, 1.0, 1.0]
        )

    def test_use_mesh_instances_option(self):
        """
        Tests using the use mesh instances option.
        """
        self.run_use_mesh_instances_tests(
            mesh_object='Cube1',
            location_offset=[1.0, 1.0, 1.0]
        )

    def test_extension(self):
        """
        Checks that the instance assets extension loaded properly.
        """
        self.run_extension_tests({
            'default': {
                'instance_assets': {
                    'properties': {
                        'place_in_active_level': False,
                        'use_mesh_instances': False,
                    },
                    'tasks': [
                        'pre_operation',
                        'post_operation',
                        'pre_mesh_export',
                        'post_import'
                    ],
                    'draws': [
                        'draw_import'
                    ]
                }
            }
        })


class TestSend2UeExtensionInstanceAssetsMannequins(
    TestSend2UeExtensionInstanceAssetsBase,
    TestSend2UeMannequins
):
    """
    Runs several test cases with the instance assets extension on the mannequin meshes.
    """

    def test_place_in_active_level_option(self):
        """
        Tests using place in active level option.
        """
        self.run_instance_asset_tests(
            mesh_object='SK_Mannequin_Female',
            armature_object='female_root',
            animation_name='third_person_walk_01',
            location_offset=[1.0, 1.0, 1.0]
        )
