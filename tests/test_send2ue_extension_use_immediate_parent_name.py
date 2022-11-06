from utils.base_test_case import BaseSend2ueTestCaseCore, BaseSend2ueTestCase, SkipSend2UeTests
from test_send2ue_cubes import TestSend2UeCubes
from test_send2ue_mannequins import TestSend2UeMannequins


class TestSend2UeExtensionUseImmediateParentNameBase(BaseSend2ueTestCaseCore, BaseSend2ueTestCase):
    def setup_parents(self, child_name, parent_name):
        self.blender.create_empty(parent_name)
        self.log(f'Parenting "{child_name}" to "{parent_name}"...')
        self.blender.parent_to(child_name, parent_name)

    def run_use_immediate_parent_name_option_tests(self, objects_and_collections):
        for object_name, attributes in objects_and_collections.items():
            collection_hierarchy = attributes.get('collections')
            grooms = attributes.get('grooms')
            armature = attributes.get('armature')

            self.blender.create_scene_collections(collection_hierarchy)
            self.blender.set_scene_collection_hierarchy(collection_hierarchy)
            self.move_to_collection([object_name] + armature, collection_hierarchy[-1])

            # turn use immediate parent name off
            self.blender.set_addon_property(
                'scene',
                'send2ue',
                'extensions.use_immediate_parent_name.use_immediate_parent_name',
                False)
            self.send2ue_operation()
            # check that the mesh name the object name
            self.assert_mesh_import(object_name)

            # check that the groom assets have the correct binding target mesh
            for groom in grooms:
                self.assert_binding_asset(groom, object_name)

            self.tearDown()

            # turn use immediate parent name on
            self.blender.set_addon_property(
                'scene',
                'send2ue',
                'extensions.use_immediate_parent_name.use_immediate_parent_name',
                True)

            self.send2ue_operation()

            # check that the mesh name is the parent collection
            self.assert_mesh_import(collection_hierarchy[-1])

            # check that the groom assets have the correct binding target mesh
            for groom in grooms:
                self.assert_binding_asset(groom, collection_hierarchy[-1])

        # reset blender and unreal
        self.tearDown()
        self.setUp()
        self.blender.create_scene_collections(['Export'])

        # test when mesh collection's parent is an empty type object
        for object_name, attributes in objects_and_collections.items():
            parent_hierarchy = attributes.get('collections')
            grooms = attributes.get('grooms')
            armature = attributes.get('armature')

            # create an empty type parent with name from parent_hierarchy
            self.setup_parents(object_name, parent_hierarchy[-1])
            self.move_to_collection([object_name] + armature + [parent_hierarchy[-1]], 'Export')

            # turn use immediate parent name on
            self.blender.set_addon_property(
                'scene',
                'send2ue',
                'extensions.use_immediate_parent_name.use_immediate_parent_name',
                True)

            self.send2ue_operation()

            # check that the mesh name is the parent collection
            self.assert_mesh_import(parent_hierarchy[-1])

            # check that the groom assets have the correct binding target mesh
            for groom in grooms:
                self.assert_binding_asset(groom, parent_hierarchy[-1])


class TestSend2UeExtensionUseImmediateParentNameCubes(
    SkipSend2UeTests,
    TestSend2UeCubes,
    TestSend2UeExtensionUseImmediateParentNameBase
):
    """
    Runs several test cases with the use immediate parent name extension on the cube meshes.
    """
    def test_lods(self):
        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.use_immediate_parent_name.use_immediate_parent_name',
            True)
        super().test_lods(self)

    def test_use_immediate_parent_name_option(self):
        """
        Tests using immediate parent name as asset name.
        """
        self.run_use_immediate_parent_name_option_tests(
            objects_and_collections={
                'Cube1_LOD0': {
                    'collections': ['Export', 'ParentCollectionName'],
                    'grooms': [],
                    'armature': []
                }
            })

    def test_extension(self):
        """
        Checks that the use immediate parent name extension loaded properly.
        """
        self.run_extension_tests({
            'default': {
                'use_immediate_parent_name': {
                    'properties': {
                        'use_immediate_parent_name': False,
                    },
                    'tasks': [
                        'pre_validations',
                        'pre_mesh_export',
                        'pre_import'
                    ],
                    'draws': [
                        'draw_paths'
                    ]
                }
            }
        })


class TestSend2UeExtensionUseImmediateParentNameMannequins(
    SkipSend2UeTests,
    TestSend2UeMannequins,
    TestSend2UeExtensionUseImmediateParentNameBase
):
    """
    Runs several test cases with the use immediate parent name extension on the mannequin meshes.
    """
    def test_use_immediate_parent_name_option(self):
        """
        """
        self.run_use_immediate_parent_name_option_tests(
            objects_and_collections={
                'SK_Mannequin_Female': {
                    'collections': ['Export', 'ParentCollectionName'],
                    'grooms': ['particle_hair_head'],
                    'armature': ['female_root']
                }
            })

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
                'frames': [1, 5, 14],
                'grooms': ['particle_hair_head']
            }})
