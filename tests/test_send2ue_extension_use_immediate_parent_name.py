from utils.base_test_case import BaseSend2ueTestCaseCore, BaseSend2ueTestCase, SkipSend2UeTests
from test_send2ue_cubes import TestSend2UeCubes
from test_send2ue_mannequins import TestSend2UeMannequins


class TestSend2UeExtensionUseImmediateParentNameBase(BaseSend2ueTestCaseCore, BaseSend2ueTestCase):
    def setup_parents(self, child_name, parent_name):
        self.blender.create_empty(parent_name)
        self.log(f'Parenting "{child_name}" to "{parent_name}"...')
        self.blender.parent_to(child_name, parent_name)

    def run_use_immediate_parent_name_option_tests(self, objects_and_collections):
        for object_name, collection_hierarchy in objects_and_collections.items():
            self.blender.create_scene_collections(collection_hierarchy)
            self.blender.set_scene_collection_hierarchy(collection_hierarchy)
            self.move_to_collection([object_name], collection_hierarchy[-1])

            # turn use immediate parent name off
            self.blender.set_addon_property(
                'scene',
                'send2ue',
                'extensions.use_immediate_parent_name.use_immediate_parent_name',
                False)
            self.send2ue_operation()
            # check that the mesh name the object name
            self.assert_mesh_import(object_name)

            # turn use immediate parent name on
            self.blender.set_addon_property(
                'scene',
                'send2ue',
                'extensions.use_immediate_parent_name.use_immediate_parent_name',
                True)

            self.send2ue_operation()

            # check that the mesh name is the parent collection
            self.assert_mesh_import(collection_hierarchy[-1])

        # reset blender and unreal
        self.tearDown()
        self.setUp()
        self.blender.create_scene_collections(['Export'])

        # test when mesh collection's parent is an empty type object
        for object_name, parent_hierarchy in objects_and_collections.items():
            # create an empty type parent with name from parent_hierarchy
            self.setup_parents(object_name, parent_hierarchy[-1])
            self.move_to_collection([object_name] + [parent_hierarchy[-1]], 'Export')

            # turn use immediate parent name on
            self.blender.set_addon_property(
                'scene',
                'send2ue',
                'extensions.use_immediate_parent_name.use_immediate_parent_name',
                True)

            self.send2ue_operation()

            # check that the mesh name is the parent collection
            self.assert_mesh_import(parent_hierarchy[-1])


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
                'Cube1_LOD0': ['Export', 'ParentCollectionName']
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
                'SK_Mannequin_Female': ['Export', 'ParentCollectionName']
            })
