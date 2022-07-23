from utils.base_test_case import BaseSend2ueTestCaseCore, SkipSend2UeTests
from test_send2ue_cubes import TestSend2UeCubes
from test_send2ue_mannequins import TestSend2UeMannequins


class TestSend2UeExtensionCombineMeshesBase(BaseSend2ueTestCaseCore):
    def setup_parents(self, children, parent_name, mesh_type):
        if mesh_type == 'static_mesh':
            self.blender.create_empty(parent_name)
            for offset, child_name in enumerate(children, 1):
                self.set_object_transforms(child_name, location=[0.0, offset * 2, 0.0])
                self.log(f'Parenting "{child_name}" to "{parent_name}"...')
                self.blender.parent_to(child_name, parent_name)

        elif mesh_type == 'skeletal_mesh':
            self.blender.separate_mesh_by_selection(children[0], children[-1])

    def run_combine_child_meshes_tests(self, asset_name, parent, children, mesh_type):
        self.setup_parents(children, parent, mesh_type)
        self.move_to_collection([parent] + children, 'Export')

        # turn combine_child_meshes off
        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.combine_meshes.combine_child_meshes',
            False
        )

        # send to unreal
        self.send2ue_operation()
        for child in children:
            self.assert_mesh_import(child)

        # reset blender and unreal
        self.tearDown()
        self.setUp()

        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'extensions.combine_meshes.combine_child_meshes',
            True
        )

        self.setup_parents(children, parent, mesh_type)
        self.move_to_collection([parent] + children, 'Export')

        # send to unreal
        self.send2ue_operation()
        self.assert_mesh_import(asset_name)

        # if this is a skeletal mesh remove the asset name from the list of children to assert against
        if mesh_type == 'skeletal_mesh':
            children.remove(asset_name)

        for child_name in children:
            self.assert_mesh_import(child_name, False)


class TestSend2UeExtensionCombineMeshesCubes(
    SkipSend2UeTests,
    TestSend2UeCubes,
    TestSend2UeExtensionCombineMeshesBase
):
    """
    Runs several test cases with the combine meshes extension on the cube meshes.
    """
    def test_combine_child_meshes_option(self):
        """
        Tests the combine child mesh option.
        https://github.com/EpicGames/BlenderTools/issues/285
        """
        self.run_combine_child_meshes_tests(
            asset_name='CombinedCubes',
            parent='CombinedCubes',
            children=['Cube1_LOD0', 'Cube1_LOD1', 'Cube1_LOD2'],
            mesh_type='static_mesh'
        )

    def test_extension(self):
        """
        Checks that the combine_meshes extension loaded properly.
        """
        self.run_extension_tests({
            'default': {
                'combine_meshes': {
                    'properties': {
                        'combine_child_meshes': False,
                    },
                    'tasks': [
                        'pre_operation',
                        'filter_objects',
                        'pre_mesh_export'
                    ],
                    'draws': [
                        'draw_export'
                    ]
                }
            }
        })


class TestSend2UeExtensionCombineMeshesMannequins(
    SkipSend2UeTests,
    TestSend2UeMannequins,
    TestSend2UeExtensionCombineMeshesBase
):
    """
    Runs several test cases with the combine meshes extension on the mannequin meshes.
    """
    def test_combine_child_meshes_option(self):
        """
        Tests the combine child mesh option.
        https://github.com/EpicGames/BlenderTools/issues/459
        """
        self.run_combine_child_meshes_tests(
            asset_name='SK_Mannequin_Female',
            parent='female_root',
            children=['SK_Mannequin_Female', 'Head'],
            mesh_type='skeletal_mesh'
        )
