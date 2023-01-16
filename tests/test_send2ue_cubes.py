from utils.base_test_case import BaseSend2ueTestCase
import unittest


class TestSend2UeCubes(BaseSend2ueTestCase):
    """
    Runs several test cases with the static cube meshes.
    """

    def __init__(self, *args, **kwargs):
        super(TestSend2UeCubes, self).__init__(*args, **kwargs)
        self.file_name = 'cubes.blend'

    @unittest.skip
    def test_animations(self):
        pass

    @unittest.skip
    def test_auto_stash_active_action_option(self):
        pass

    @unittest.skip
    def test_export_object_name_as_root_option(self):
        pass

    @unittest.skip
    def test_export_custom_property_fcurves_option(self):
        pass

    def test_default_send_to_unreal(self):
        """
        Sends a cube mesh with default settings.
        """
        self.move_to_collection(['Cube1'], 'Export')
        self.send2ue_operation()
        self.assert_mesh_import('Cube1')

    def test_bulk_send_to_unreal(self):
        """
        Sends multiple cubes to unreal at once.
        """
        self.move_to_collection(['Cube1', 'Cube2'], 'Export')
        self.send2ue_operation()
        self.assert_mesh_import('Cube1')
        self.assert_mesh_import('Cube2')

    def test_lods(self):
        """
        Sends both cube meshes with lods to unreal.
        """
        cube1s = ['Cube1_LOD0', 'Cube1_LOD1', 'Cube1_LOD2']
        cube2s = ['Cube2_lod0_mesh', 'Cube2_lod1_mesh', 'Cube2_lod2_mesh']
        lod_build_settings = {
            'recompute_normals': True,
            'recompute_tangents': True,
            'use_mikk_t_space': True,
            'remove_degenerates': True
        }

        self.run_lod_tests('Cube1', cube1s, lod_build_settings, 'static')

        # make sure that the import area is clean so assets don't overwrite each other
        self.tearDown()

        self.run_lod_tests('Cube2', cube2s, lod_build_settings, 'static')

    def test_sockets(self):
        """
        Sends a Cube with sockets to unreal.
        https://github.com/EpicGames/BlenderTools/issues/69
        """
        self.run_socket_tests({
            'Cube2': ['SOCKET_socket_01', 'SOCKET_socket_02']
        })

    def test_collisions(self):
        """
        Sends a Cube with complex collisions to unreal.
        https://github.com/EpicGames/BlenderTools/issues/22
        https://github.com/EpicGames/BlenderTools/issues/359
        """
        self.run_collision_tests([
            {'Cube1': {
                'convex_count': 0,
                'simple_count': 1,
                'objects': ['UBX_Cube1']
            }},
            {'Cube1': {
                'convex_count': 0,
                'simple_count': 2,
                'objects': ['UBX_Cube1_01', 'UBX_Cube1_02']
            }},
            {'Cube1': {
                'convex_count': 0,
                'simple_count': 1,
                'objects': ['UCP_Cube1']
            }},
            {'Cube1': {
                'convex_count': 0,
                'simple_count': 1,
                'objects': ['USP_Cube1']
            }},
            {'Cube1': {
                'convex_count': 1,
                'simple_count': 0,
                'objects': ['UCX_Cube1']
            }},
        ])

    def test_materials(self):
        """
        Sends a Cube with materials to unreal.
        """
        self.run_material_tests({
            'Cube1_LOD0': {
                'asset': 'Cube1_LOD0',
                'materials': {
                    'Material': 0,
                    'blue': 1,
                    'red': 2,
                    'green': 3,
                }
            },
            'Cube2_lod0_mesh': {
                'asset': 'Cube2_lod0_mesh',
                'materials': {
                    'unreal': 0,
                    'Material': 1
                }
            },
        })

    def test_textures(self):
        """
        Sends a Cube with a textured material to unreal.
        https://github.com/EpicGames/BlenderTools/issues/83
        """
        self.run_texture_tests({
            'Cube2_lod0_mesh': ['unreal-engine-logo'],
        })

    def test_use_object_origin_option(self):
        """
        Offsets Cube1_LOD0 and tests with the use_object_origin option on and off.
        https://github.com/EpicGames/BlenderTools/issues/223
        """
        self.run_use_object_origin_option_tests(
            mesh_object='Cube1'
        )
