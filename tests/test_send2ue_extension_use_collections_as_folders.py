from utils.base_test_case import BaseSend2ueTestCaseCore, BaseSend2ueTestCase, SkipSend2UeTests
from test_send2ue_cubes import TestSend2UeCubes
from test_send2ue_mannequins import TestSend2UeMannequins


class TestSend2UeExtensionCollectionsAsFoldersBase(BaseSend2ueTestCaseCore, BaseSend2ueTestCase):
    def run_use_collections_as_folders_option_tests(self, objects_and_collections):
        for object_name, collection_hierarchy in objects_and_collections.items():
            self.blender.create_scene_collections(collection_hierarchy)
            self.blender.set_scene_collection_hierarchy(collection_hierarchy)
            self.move_to_collection([object_name], collection_hierarchy[-1])

            # turn use collections as folders off
            self.blender.set_addon_property(
                'scene',
                'send2ue',
                'extensions.use_collections_as_folders.use_collections_as_folders',
                False)
            self.send2ue_operation()
            # check that the mesh name the object name
            self.assert_mesh_import(object_name)

            # turn use collections as folders on
            self.blender.set_addon_property(
                'scene',
                'send2ue',
                'extensions.use_collections_as_folders.use_collections_as_folders',
                True)
            self.send2ue_operation()

            # check that the mesh name is the parent collection
            mesh_folder_path = self.blender.get_addon_property('scene', 'send2ue', 'unreal_mesh_folder_path')
            folder_path = mesh_folder_path + '/'.join(collection_hierarchy[1:]) + '/'
            self.assert_asset_exists(object_name, folder_path, True)


class TestSend2UeExtensionCollectionsAsFoldersCubes(
    SkipSend2UeTests,
    TestSend2UeCubes,
    TestSend2UeExtensionCollectionsAsFoldersBase
):
    """
    Runs several test cases with the use collections as folders extension on the cube meshes.
    """

    def test_lods(self):
        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.use_collections_as_folders.use_collections_as_folders',
            True)
        super().test_lods(self)

    def test_use_collections_as_folders_option(self):
        """
        Tests using collections as folders.
        """
        self.run_use_collections_as_folders_option_tests(
            objects_and_collections={
                'Cube1_LOD0': ['Export', 'SomeFolder', 'Another']
            })

    def test_extension(self):
        """
        Checks that the use collections as folders extension loaded properly.
        """
        self.run_extension_tests({
            'default': {
                'use_collections_as_folders': {
                    'properties': {
                        'use_collections_as_folders': False,
                    },
                    'tasks': [
                        'pre_import'
                    ],
                    'draws': [
                        'draw_paths'
                    ]
                }
            }
        })


class TestSend2UeExtensionCollectionsAsFoldersMannequins(
    SkipSend2UeTests,
    TestSend2UeMannequins,
    TestSend2UeExtensionCollectionsAsFoldersBase
):
    """
    Runs several test cases with the use collections as folders extension on the mannequin meshes.
    """

    def test_use_collections_as_folders_option(self):
        """
        Tests using collections as folders option.
        """
        self.move_to_collection(['female_root', 'SK_Mannequin_Female'], 'Export')
        self.run_use_collections_as_folders_option_tests(
            objects_and_collections={
                'SK_Mannequin_Female': ['Export', 'SomeFolder', 'Another']
            })
