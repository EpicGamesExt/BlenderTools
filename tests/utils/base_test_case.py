import math
import os
import collections
import sys
import unittest


class BaseTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(BaseTestCase, self).__init__(*args, **kwargs)
        self.blender_addons = list(filter(None, os.environ.get('BLENDER_ADDONS', '').split(',')))
        self.file_name = None

        self.test_environment = os.environ.get('TEST_ENVIRONMENT')
        self.test_folder = os.environ.get('HOST_TEST_FOLDER')
        self.repo_folder = os.environ.get('HOST_REPO_FOLDER')
        if self.test_environment:
            self.test_folder = os.environ.get('CONTAINER_TEST_FOLDER')
            self.repo_folder = os.environ.get('CONTAINER_REPO_FOLDER')
        self.addons_folder = os.path.join(self.repo_folder, 'release')

        sys.path.append(self.repo_folder)
        import send2ue
        import ue2rigify
        self.send2ue = send2ue
        self.ue2rigify = ue2rigify

        from utils.blender import BlenderRemoteCalls
        from send2ue.dependencies.unreal import UnrealRemoteCalls
        self.blender = BlenderRemoteCalls
        self.unreal = UnrealRemoteCalls

    def setUp(self):
        # load in the object from the file you will run tests with
        if self.file_name:
            self.blender.open_file(self.test_folder, self.file_name)
        # or just load the default
        else:
            self.blender.open_default()

        if os.environ.get('TEST_ENVIRONMENT'):
            self.blender.install_addons(self.repo_folder, self.blender_addons)
            self.blender.send2ue_setup_project()
        else:
            for addon_name in self.blender_addons:
                self.blender.register_addon(addon_name)

        self.blender.set_addon_property('scene', 'send2ue', 'active_settings_template', 'default.json')

    @staticmethod
    def log(message):
        print(message)

    @staticmethod
    def get_rounded_values(some_list, decimals=1):
        return [round(i, decimals) for i in some_list]

    @staticmethod
    def convert_blender_to_unreal_transforms(transforms, decimals=2):
        """
        Converts blender transforms to unreal transforms.

        :param dict transforms: A dictionary of location, rotation, and scale.
        :param int decimals: How many decimals to round each value to.
        :return dict: A dictionary of location, rotation, and scale.
        """
        location = transforms.get('location')
        if location:
            transforms['location'] = [
                round(location[0] * 100, decimals),
                -round(location[1] * 100, decimals),
                round(location[2] * 100, decimals)
            ]
        rotation = transforms.get('rotation')
        if rotation:
            transforms['rotation'] = [
                round(math.degrees(rotation[0]), decimals),
                -round(math.degrees(rotation[1]), decimals),
                round(math.degrees(rotation[2]), decimals)
            ]
        scale = transforms.get('scale')
        if scale:
            transforms['scale'] = [
                round(scale[0], decimals),
                -round(scale[1], decimals),
                round(scale[2], decimals)
            ]

        return transforms

    @staticmethod
    def convert_unreal_to_blender_transforms(transforms, decimals=2):
        """
        Converts unreal transforms to blender transforms.

        :param dict transforms: A dictionary of location, rotation, and scale.
        :param int decimals: How many decimals to round each value to.
        :return dict: A dictionary of location, rotation, and scale.
        """
        location = transforms.get('location')
        if location:
            transforms['location'] = [
                round(location[0] / 100, decimals),
                -round(location[1] / 100, decimals),
                round(location[2] / 100, decimals)
            ]
        rotation = transforms.get('rotation')
        if rotation:
            transforms['rotation'] = [
                round(math.radians(rotation[0]), decimals),
                -round(math.radians(rotation[1]), decimals),
                round(math.radians(rotation[2]), decimals)
            ]
        scale = transforms.get('scale')
        if scale:
            transforms['scale'] = [
                round(scale[0], decimals),
                -round(scale[1], decimals),
                round(scale[2], decimals)
            ]

        return transforms


class BaseSend2ueTestCaseCore(BaseTestCase):
    """
    Base test cases for core features of send to unreal
    """

    def __init__(self, *args, **kwargs):
        super(BaseSend2ueTestCaseCore, self).__init__(*args, **kwargs)
        self.addon_name = 'send2ue'

    def setUp(self):
        super().setUp()
        self.set_extension_repo('')

    def set_extension_repo(self, path):
        self.log(f'Setting the addon extension repo to "{path}"')

        # make the path a linux path if in the test environment
        if self.test_environment:
            path = os.path.normpath(path).replace(os.path.sep, '/')

        self.blender.set_addon_property(
            'preferences',
            self.addon_name,
            'extensions_repo_path',
            path
        )
        self.blender.run_addon_operator(self.addon_name, 'reload_extensions')

    def assert_extension_operators(self, extension_name, extension_operators, exists=True):
        self.log(f'Running all {self.addon_name} {extension_name} extension utility operators...')
        for extension_operator in extension_operators:
            try:
                self.blender.run_addon_operator(self.addon_name, extension_operator)
            except AttributeError:
                self.assertFalse(
                    exists,
                    f'The "{extension_name}" extension operator "{extension_operator}" does not exist.'
                )

    def assert_extension_properties(self, extension_name, extension_properties, exists=True):
        self.log(f'Checking {self.addon_name} {extension_name} extension properties...')
        for name, default_value in extension_properties.items():
            value = self.blender.get_addon_property(
                'scene',
                self.addon_name,
                f'extensions.{extension_name}.{name}'
            )
            if not exists:
                self.assertEqual(
                    value,
                    None,
                    f'The "{extension_name}" extension property "{name}" exists when it should not.'
                )

            if exists:
                self.assertEqual(
                    value,
                    default_value,
                    f'The "{extension_name}" extension property "{name}" value "{value}" does not equal the default '
                    f'value "{default_value}".'
                )

    def assert_extension_method(self, extension_name, extension_methods, exists=True):
        self.log(f'Checking {self.addon_name} {extension_name} extension draws...')
        for extension_method in extension_methods:
            value = self.blender.has_addon_property(
                'scene',
                self.addon_name,
                f'extensions.{extension_name}.{extension_method}'
            )
            if exists:
                self.assertTrue(
                    value,
                    f'The "{extension_name}" extension method "{extension_method}" was not found.'
                )
            else:
                self.assertFalse(
                    value,
                    f'The "{extension_name}" extension method "{extension_method}" should not exist.'
                )

    def assert_extension(self, extension_name, extensions_data, exists=True):
        extension_properties = extensions_data.get('properties', {})
        extension_tasks = extensions_data.get('tasks', [])
        extension_utility_operators = extensions_data.get('utility_operators', [])
        extension_draws = extensions_data.get('draws', [])

        # check properties
        self.assert_extension_properties(extension_name, extension_properties, exists)

        # check tasks
        self.assert_extension_method(extension_name, extension_tasks, exists)

        # check utility operators
        self.assert_extension_operators(extension_name, extension_utility_operators)

        # check draws
        self.assert_extension_method(extension_name, extension_draws, exists)

    def run_extension_tests(self, extensions):
        external_extensions = extensions.get('external', {})
        default_extensions = extensions.get('default', {})

        # check that all the extensions exist
        self.set_extension_repo(os.path.join(self.test_folder, 'test_files', 'send2ue_extensions'))
        self.setUp()
        for extension_name, extensions_data in {**external_extensions, **default_extensions}.items():
            self.assert_extension(extension_name, extensions_data)

        # reload blank scene and check again
        # https://github.com/EpicGames/BlenderTools/issues/395
        self.setUp()
        for extension_name, extensions_data in {**external_extensions, **default_extensions}.items():
            self.assert_extension(extension_name, extensions_data)

        # check that external extensions are removed are being removed correctly
        self.set_extension_repo('')
        for extension_name, extensions_data in external_extensions.items():
            self.assert_extension(extension_name, extensions_data, False)

    def run_template_tests(self, templates):
        for template_name, properties in templates.items():
            # check that template loading functions correctly
            self.log(f'Testing loading template "{template_name}"...')
            file_path = os.path.join(self.test_folder, 'test_files', 'send2ue_templates', template_name)
            # make the path a linux path if in the test environment
            if self.test_environment:
                file_path = os.path.normpath(file_path).replace(os.path.sep, '/')

            self.blender.run_addon_operator(self.addon_name, 'load_template', None, {'filepath': file_path})
            self.blender.set_addon_property('scene', self.addon_name, 'active_settings_template', template_name)
            for name, value in properties.items():
                self.log(f'Checking property "{name}"...')
                property_value = self.blender.get_addon_property(
                    'scene',
                    self.addon_name,
                    name
                )
                self.assertEqual(
                    property_value,
                    value,
                    f'The {template_name} failed to set {name} to value {value}'
                )

            # check that template removal functions correctly
            self.blender.run_addon_operator(self.addon_name, 'remove_template')
            tool_info = self.send2ue.constants.ToolInfo
            template = self.send2ue.constants.Template
            if template_name != template.DEFAULT:
                self.log(f'Removing template "{template_name}"...')
                self.assertFalse(
                    self.blender.has_temp_file([
                        tool_info.APP.value,
                        tool_info.NAME.value,
                        template.NAME,
                        template_name
                    ]),
                    f'The template "{template_name}" still exists when it should have been removed.'
                )

    def run_import_asset_operator_tests(self, asset_files):
        for asset_file, object_names in asset_files.items():

            self.log(f'Running import asset operation on FBX file "{asset_file}"...')
            file_path = os.path.join(self.test_folder, 'test_files', 'fbx_files', asset_file)

            # make the path a linux path if in the test environment
            if self.test_environment:
                file_path = os.path.normpath(file_path).replace(os.path.sep, '/')

            self.blender.run_addon_operator('wm', 'import_asset', [], {'filepath': file_path})
            for object_name in object_names:
                self.assertTrue(
                    self.blender.has_data_block('objects', object_name),
                    f'The object {object_name} does not exits when it should have been imported.'
                )
                transforms = self.blender.get_object_transforms(object_name, None)
                location = transforms.get('location')
                rotation = transforms.get('rotation')
                scale = transforms.get('scale')

                self.assertEqual(
                    location,
                    [0, 0, 0],
                    f'{object_name} has a location of {location} when it should be [0, 0, 0]'
                )
                self.assertEqual(
                    rotation,
                    [0, 0, 0],
                    f'{object_name} has a location of {location} when it should be [0, 0, 0]'
                )
                self.assertEqual(
                    scale,
                    [1, 1, 1],
                    f'{object_name} has a location of {location} when it should be [1, 1, 1]'
                )

    def run_scene_data_persistence_tests(self, file_name, property_data):
        # open a default blend file
        self.blender.open_default()

        # set some non-default property values
        for property_name, values in property_data.items():
            self.blender.set_addon_property('scene', 'send2ue', property_name, values['non-default'])

        # save that file
        self.blender.save_file(self.test_folder, file_name)

        # open a new default blend file again
        self.blender.open_default()

        # assert the values are default
        for property_name, values in property_data.items():
            value = values['default']
            self.assertEqual(
                self.blender.get_addon_property('scene', 'send2ue', property_name),
                value,
                f'{property_name} is not equal to the default value {value}'
            )

        # now open the file previously saved
        self.blender.open_file(self.test_folder, file_name)

        # assert the values are non-default
        for property_name, values in property_data.items():
            value = values['non-default']
            self.assertEqual(
                self.blender.get_addon_property('scene', 'send2ue', property_name),
                value,
                f'{property_name} is not equal to the default value {value}'
            )

        # open a new default blend file again
        self.blender.open_default()

        # delete the created blend
        self.blender.delete_file(self.test_folder, file_name)


class BaseSend2ueTestCase(BaseTestCase):
    def setUp(self):
        super(BaseSend2ueTestCase, self).setUp()

        # delete all actors from the unreal level
        self.unreal.delete_all_asset_actors()

        # delete all folders
        for property_name in [
            'unreal_mesh_folder_path',
            'unreal_animation_folder_path',
            'unreal_groom_folder_path'
        ]:
            unreal_folder_path = self.blender.get_addon_property('scene', 'send2ue', property_name)
            self.unreal.delete_directory(unreal_folder_path)

        # create the export collection
        self.blender.create_predefined_collections()
        self.blender.set_addon_property('scene', 'send2ue', 'import_animations', False)

    def tearDown(self):
        # delete all actors from the unreal level
        self.unreal.delete_all_asset_actors()

        # delete all folders
        for property_name in [
            'unreal_mesh_folder_path',
            'unreal_animation_folder_path',
            'unreal_groom_folder_path'
        ]:
            unreal_folder_path = self.blender.get_addon_property('scene', 'send2ue', property_name)
            self.unreal.delete_directory(unreal_folder_path)

    def assert_asset_exists(self, asset_name, folder_path, exists=True):
        if exists:
            self.log(f'Ensuring that "{asset_name}" exists...')
            self.assertTrue(
                self.unreal.asset_exists(f'{folder_path}{asset_name}'),
                f'The "{asset_name}" does not exist in unreal!'
            )
        else:
            self.log(f'Ensuring that "{asset_name}" does not exist...')
            self.assertFalse(
                self.unreal.asset_exists(f'{folder_path}{asset_name}'),
                f'The "{asset_name}" exists in unreal when it should not!'
            )

    def assert_mesh_import(self, asset_name, exists=True):
        folder_path = self.blender.get_addon_property('scene', 'send2ue', 'unreal_mesh_folder_path')
        self.assert_asset_exists(asset_name, folder_path, exists)

    def assert_animation_import(self, asset_name, exists=True):
        folder_path = self.blender.get_addon_property('scene', 'send2ue', 'unreal_animation_folder_path')
        self.assert_asset_exists(asset_name, folder_path, exists)

    def assert_curves_removal(self, mesh_name, curves_names):
        self.log(f'Ensuring that particles converted from curves objects do not exist post operation...')

        curves_names = self.blender.check_particles(mesh_name, curves_names)

        if curves_names:
            curves_names_string = ', '.join(name for name in curves_names)
            self.assertFalse(
                len(curves_names) == 0,
                f'{curves_names_string} exist(s) on {mesh_name} when they should not!'
            )

    def assert_groom_import(self, asset_name, exists=True):
        folder_path = self.blender.get_addon_property('scene', 'send2ue', 'unreal_groom_folder_path')
        self.assert_asset_exists(asset_name, folder_path, exists)

    def assert_binding_asset(self, groom_asset_name, target_mesh_name, mesh_folder_path=None):
        self.log(f'Checking that binding asset is created correctly for "{groom_asset_name}"...')

        binding_asset_name = f'{groom_asset_name}_{target_mesh_name}_Binding'

        if not mesh_folder_path:
            mesh_folder_path = self.blender.get_addon_property('scene', 'send2ue', 'unreal_mesh_folder_path')
        groom_folder_path = self.blender.get_addon_property('scene', 'send2ue', 'unreal_groom_folder_path')

        self.assert_asset_exists(binding_asset_name, groom_folder_path, True)

        groom_assert_path = groom_folder_path + groom_asset_name
        target_mesh_path = mesh_folder_path + target_mesh_name
        binding_asset_path = groom_folder_path + binding_asset_name

        self.assertTrue(
            self.unreal.has_binding_groom_asset(binding_asset_path, groom_assert_path),
            f'The groom asset "{groom_asset_name}" is not set for "{binding_asset_name}"!'
        )
        self.assertTrue(
            self.unreal.has_binding_target(binding_asset_path, target_mesh_path),
            f'The target mesh "{target_mesh_name}" is not set for "{binding_asset_name}"!'
        )

    def assert_blueprint_asset(self, asset_name, exists=True):
        folder_path = self.blender.get_addon_property('scene', 'send2ue', 'unreal_mesh_folder_path')
        self.assert_asset_exists(asset_name, folder_path, exists)

    def assert_blueprint_with_groom(self, blueprint_asset_name, groom_asset_name, binding_asset_name, mesh_asset_name):
        self.log(f'Checking that groom component "{groom_asset_name}" and mesh component "{mesh_asset_name}" '
                 f'are created correctly for "{blueprint_asset_name}"...')

        mesh_folder_path = self.blender.get_addon_property('scene', 'send2ue', 'unreal_mesh_folder_path')
        groom_folder_path = self.blender.get_addon_property('scene', 'send2ue', 'unreal_groom_folder_path')

        groom_path = groom_folder_path + groom_asset_name
        binding_path = groom_folder_path + binding_asset_name
        mesh_path = mesh_folder_path + mesh_asset_name
        blueprint_path = mesh_folder_path + blueprint_asset_name

        self.assertTrue(
            self.unreal.has_groom_component(blueprint_path, binding_path, groom_path),
            f'The groom component "{groom_asset_name}" on blueprint asset "{blueprint_asset_name}" does not exist '
            f'or have incorrect assets assigned"!'
        )

        self.assertTrue(
            self.unreal.has_mesh_component(blueprint_path, mesh_path),
            f'The skeletal mesh component "{mesh_asset_name}" on blueprint asset "{blueprint_asset_name}" does not '
            f'exist or have incorrect assets assigned"!'
        )

        self.assertTrue(
            self.unreal.has_groom_and_mesh_components(blueprint_path, binding_path, groom_path, mesh_path),
            f'Component "{groom_asset_name}" is not correctly parented under "{mesh_asset_name}"!'
        )

    def assert_mesh_origin(self, asset_name, origin):
        self.log(f'Checking "{asset_name}" for matching origins...')
        folder_path = self.blender.get_addon_property('scene', 'send2ue', 'unreal_mesh_folder_path')
        asset_path = f'{folder_path}{asset_name}'
        unreal_origin = self.get_rounded_values(self.unreal.get_origin(asset_path))
        unreal_origin = self.send2ue.utilities.convert_unreal_to_blender_location(unreal_origin)

        self.assertTrue(
            collections.Counter(unreal_origin) == collections.Counter(origin),
            (
                f'The unreal origin {unreal_origin} of "{asset_name}" does not match the origin '
                f'{origin}'
            )
        )

    def assert_actor_location(self, actor_name, location_offset, exists):
        transforms = self.unreal.get_asset_actor_transforms(actor_name)

        if not exists:
            self.assertEqual(
                transforms,
                None,
                f'An actor "{actor_name}" was found in the active level when it should not exist'
            )
        else:
            actor_location = self.send2ue.utilities.convert_unreal_to_blender_location(transforms['location'])
            self.assertEqual(
                location_offset,
                actor_location,
                f'The actor "{actor_name}" has a location of {actor_location} while in blender it is {location_offset}.'
            )

    def assert_socket(self, asset_name, socket_name):
        self.log(f'Checking "{asset_name}" for socket "{socket_name}"...')
        folder_path = self.blender.get_addon_property('scene', 'send2ue', 'unreal_mesh_folder_path')
        asset_path = f'{folder_path}{asset_name}'
        self.assertTrue(
            self.unreal.has_socket(asset_path, socket_name),
            f'The socket "{socket_name}" could not be found on "{asset_name}" in unreal.'
        )
        self.assertTrue(
            self.unreal.has_socket_outer(asset_path, socket_name),
            f'The socket "{socket_name}" is not owned by "{asset_name}" in unreal.'
        )

    def assert_collision(self, asset_name, simple_count=0, convex_count=0):
        self.log(f'Checking "{asset_name}" for collision...')
        folder_path = self.blender.get_addon_property('scene', 'send2ue', 'unreal_mesh_folder_path')
        asset_path = f'{folder_path}{asset_name}'
        collision_info = self.unreal.get_static_mesh_collision_info(asset_path)

        self.assertTrue(
            collision_info.get('customized'),
            f'The mesh "{asset_name}" does not have a customized collision.'
        )
        self.assertEqual(
            convex_count,
            collision_info.get('convex'),
            f'The convex collision count is not correct.'
        )
        self.assertEqual(
            simple_count,
            collision_info.get('simple'),
            f'The simple collision count is not correct.'
        )

    def assert_material(self, asset_name, material_name, material_index, exists):
        self.log(f'Checking for material slot "{material_name}" on "{asset_name}"...')
        folder_path = self.blender.get_addon_property('scene', 'send2ue', 'unreal_mesh_folder_path')
        asset_path = f'{folder_path}{asset_name}'
        unreal_material_index = self.unreal.get_material_index_by_name(asset_path, material_name)
        self.assertEqual(
            material_index,
            unreal_material_index,
            f'The material index {unreal_material_index} on {asset_name} was not on {asset_name} in unreal.'
        )
        material_asset_path = f'{folder_path}{material_name}'
        self.log(f'Checking for material asset "{material_name}" in unreal...')
        if exists:
            self.assertTrue(
                self.unreal.asset_exists(material_asset_path),
                f'The material "{material_name}" does not exist in unreal.'
            )
        else:
            self.assertFalse(
                self.unreal.asset_exists(material_asset_path),
                f'The material "{material_name}" exists in unreal when it should not.'
            )

    def assert_texture(self, texture_name, exists):
        self.log(f'Checking for texture "{texture_name}"...')
        folder_path = self.blender.get_addon_property('scene', 'send2ue', 'unreal_mesh_folder_path')
        texture_asset_path = f'{folder_path}{texture_name}'
        if exists:
            self.assertTrue(
                self.unreal.asset_exists(texture_asset_path),
                f'The texture "{texture_name}" does not exist in unreal.'
            )
        else:
            self.assertFalse(
                self.unreal.asset_exists(texture_asset_path),
                f'The texture "{texture_name}" exists in unreal when it should not.'
            )

    def assert_export_all_actions(self, animation_names):
        """
        Assert export all actions option.
        """
        # send to unreal with import animation off
        self.blender.set_addon_property('scene', 'send2ue', 'import_animations', False)
        self.send2ue_operation()
        for animation_name in animation_names:
            self.assert_animation_import(animation_name, False)

        self.blender.set_addon_property('scene', 'send2ue', 'import_animations', True)
        self.blender.set_addon_property('scene', 'send2ue', 'export_all_actions', True)
        self.blender.set_addon_property('scene', 'send2ue', 'export_object_name_as_root', True)
        self.send2ue_operation()
        for animation_name in animation_names:
            self.assert_animation_import(animation_name, True)

    def assert_animation_only_import(self, object_name, animation_names, groom_names):
        """
        Assert a animation only import.
        """
        self.blender.set_addon_property('scene', 'send2ue', 'import_meshes', False)
        self.blender.set_addon_property('scene', 'send2ue', 'import_animations', True)
        self.blender.set_addon_property('scene', 'send2ue', 'import_grooms', False)

        self.send2ue_operation()
        self.log(f'Checking that only animations were imported when other import options are off...')

        self.assert_mesh_import(object_name, False)
        for groom_name in groom_names:
            self.assert_groom_import(groom_name, False)
        for animation_name in animation_names:
            self.assert_animation_import(animation_name, True)

        self.tearDown()

        self.blender.set_addon_property('scene', 'send2ue', 'import_animations', True)
        self.remove_from_collection([object_name], 'Export')
        self.send2ue_operation()
        self.log(f'Checking that only animations were imported...')
        self.assert_mesh_import(object_name, False)
        for animation_name in animation_names:
            self.assert_animation_import(animation_name, True)

    def assert_muted_tracks(self, rig_name, animation_names):
        """
        Assert for only unmuted actions.
        """
        self.blender.set_addon_property('scene', 'send2ue', 'export_all_actions', False)
        for index, animation_name in enumerate(animation_names):
            mute_value = not bool(index)
            self.log(f'Setting mute value to "{mute_value}" for action "{animation_name}"...')
            self.blender.set_all_action_attributes(rig_name, {animation_name: {'mute': mute_value}})

        self.send2ue_operation()

        for index, animation_name in enumerate(animation_names):
            self.assert_animation_import(animation_name, bool(index))

    def assert_solo_track(self, rig_name, animation_names):
        """
        Assert for only the action on the solo track.
        """
        self.blender.set_addon_property('scene', 'send2ue', 'import_animations', True)
        self.blender.set_addon_property('scene', 'send2ue', 'export_all_actions', False)
        self.blender.stash_animation_data(rig_name)
        for animation_name in animation_names:
            self.log(f'Checking for only solo action "{animation_name}"...')
            self.blender.set_all_action_attributes(rig_name, {animation_name: {'is_solo': True}})
            break
        self.send2ue_operation()
        for index, animation_name in enumerate(animation_names):
            self.assert_animation_import(animation_name, not bool(index))

    def assert_morph_targets(self, skeletal_mesh_name, morph_targets):
        folder_path = self.blender.get_addon_property('scene', 'send2ue', 'unreal_mesh_folder_path')
        self.log(f'Checking skeletal mesh "{skeletal_mesh_name}" for morph targets "{morph_targets}"...')
        asset_path = f'{folder_path}{skeletal_mesh_name}'
        unreal_morph_target_names = self.unreal.get_morph_target_names(asset_path)
        for morph_target in morph_targets:
            self.assertTrue(
                morph_target in unreal_morph_target_names,
                f'No morph target "{morph_target}" exists on skeletal mesh "{skeletal_mesh_name}"!'
            )

    def assert_curve(self, animation_name, curve_name, exists=True):
        folder_path = self.blender.get_addon_property('scene', 'send2ue', 'unreal_animation_folder_path')
        self.log(f'Checking animation "{animation_name}" for curve "{curve_name}"...')
        asset_path = f'{folder_path}{animation_name}'
        result = self.unreal.does_curve_exist(asset_path, curve_name)
        if exists:
            self.assertTrue(result, f'No curve "{curve_name}" exists on animation "{animation_name}"!')
        else:
            self.assertFalse(result, f'Curve "{curve_name}" exists on animation "{animation_name}" when it should not!')

    def assert_animation_hierarchy(self, rig_name, animation_name, bone_name, include_object=True):
        self.log(
            f'Checking the bone hierarchy of "{animation_name}" to see if "{bone_name}" has the same path '
            f'to the root bone...'
        )

        folder_path = self.blender.get_addon_property('scene', 'send2ue', 'unreal_animation_folder_path')
        asset_path = f'{folder_path}{animation_name}'
        unreal_bone_path = self.unreal.get_bone_path_to_root(asset_path, bone_name)
        blender_bone_path = self.blender.get_bone_path_to_root(rig_name, bone_name, include_object)

        self.assertEqual(
            collections.Counter(blender_bone_path),
            collections.Counter(unreal_bone_path),
            f'The blender bone path to the root {blender_bone_path} does not match {unreal_bone_path} in unreal!'
        )

    def assert_animation_translation(self, rig_name, animation_name, bone_name, frame, offset_amount=None):
        self.log(f'Checking "{animation_name}" to see if "{bone_name}" is in the same world location at frame {frame}')
        folder_path = self.blender.get_addon_property('scene', 'send2ue', 'unreal_animation_folder_path')
        asset_path = f'{folder_path}{animation_name}'

        unreal_result = self.unreal.get_bone_transform_for_frame(asset_path, bone_name, frame - 1)
        unreal_result['location'] = unreal_result.get('world_location')
        unreal_world_location = self.convert_unreal_to_blender_transforms(unreal_result).get('location')
        blender_world_location = self.blender.get_world_bone_translation_for_frame(
            rig_name,
            bone_name,
            animation_name,
            frame
        )
        # apply the offset to the comparison
        if offset_amount:
            blender_world_location = [
                round(blender_value-offset_value, 2) for blender_value, offset_value in zip(
                    blender_world_location,
                    offset_amount
                )
            ]

        self.assertTrue(
            collections.Counter(unreal_world_location) == collections.Counter(blender_world_location),
            (
                f'The unreal translation {unreal_world_location} of bone "{bone_name}" does not match the translation '
                f'{blender_world_location} of bone "{bone_name}" at frame {frame} in animation "{animation_name}".'
            )
        )

    def send2ue_operation(self):
        self.log('Running the Send to Unreal operation...')
        self.blender.send2ue()

    def set_object_transforms(self, object_name, location=None, rotation=None, scale=None):
        transforms = {}
        if location:
            transforms['location'] = location
            self.log(f'Setting the location of "{object_name}" to {location}')
        if rotation:
            transforms['rotation'] = rotation
            self.log(f'Setting the rotation of "{object_name}" to {rotation}')
        if scale:
            transforms['scale'] = scale
            self.log(f'Setting the scale of "{object_name}" to {scale}')

        self.blender.set_object_transforms(object_name, transforms)

    def set_select_particles_visible(self, mesh_name, particles):
        enabled_names = particles.get('enabled')
        disabled_names = particles.get('disabled')
        all_names = enabled_names + disabled_names

        if all_names:
            all_names_string = ', '.join(name for name in all_names)
            self.log(f'Setting {all_names_string} on {mesh_name} invisible in viewport')
            self.blender.set_particles_visible(mesh_name, all_names, False)

        if enabled_names:
            enabled_names_string = ', '.join(name for name in enabled_names)
            self.log(f'Setting {enabled_names_string} on {mesh_name} visible in viewport')
            self.blender.set_particles_visible(mesh_name, enabled_names)

    def move_to_collection(self, object_names, collection_name):
        for object_name in object_names:
            self.log(f'Moving "{object_name}" to "{collection_name}" collection...')
            self.blender.move_to_collection(object_name, collection_name)

    def remove_from_collection(self, object_names, collection_name):
        for object_name in object_names:
            self.log(f'removing "{object_name}" from "{collection_name}" collection...')
            self.blender.remove_from_collection(object_name, collection_name)

    def run_skeleton_tests(self, object_name):
        """
        https://github.com/EpicGames/BlenderTools/issues/249
        This feature allows swapping out meshes on existing skeletons.
        """
        folder_path = self.blender.get_addon_property('scene', 'send2ue', 'unreal_mesh_folder_path')
        skeleton_name = f'{object_name}_Skeleton'
        test_folder = '/Game/test/'
        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'unreal_mesh_folder_path',
            test_folder
        )
        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'unreal_skeleton_asset_path',
            f'{folder_path}{skeleton_name}'
        )
        self.send2ue_operation()

        # check if the skeletal mesh exists in the unreal project
        self.assert_mesh_import(object_name)

        # check that the skeleton does not exist in the unreal project since it should've used the existing one
        self.assertFalse(
            self.unreal.asset_exists(f'{test_folder}{skeleton_name}'),
            f'The skeleton exists in unreal {test_folder}{skeleton_name} here when it should have been referencing '
            f'the skeleton here {folder_path}{skeleton_name}'
        )

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
            'use_object_origin',
            False
        )
        location_offset = [1.0, 1.0, 1.0]

        if armature_object:
            self.move_to_collection([mesh_object, armature_object], 'Export')
            self.set_object_transforms(armature_object, location=location_offset)
            self.blender.set_all_action_locations(location_offset)
            self.blender.set_addon_property('scene', 'send2ue', 'import_animations', True)
        else:
            self.move_to_collection([mesh_object], 'Export')
            self.set_object_transforms(mesh_object, location=location_offset)

        self.send2ue_operation()

        if armature_object:
            self.assert_animation_translation(armature_object, animation_name, bone_name, frame)
        else:
            self.assert_mesh_origin(mesh_object, location_offset)

        # make sure that the import area is clean so assets don't overwrite each other
        self.tearDown()

        # turn object origin on
        self.blender.set_addon_property(
            'scene',
            'send2ue',
            'use_object_origin',
            True
        )

        location = [0.0, 0.0, 0.0]
        self.send2ue_operation()
        if armature_object:
            self.assert_animation_translation(
                armature_object,
                animation_name,
                bone_name,
                frame,
                offset_amount=location_offset
            )
        else:
            self.assert_mesh_origin(mesh_object, location)

    def run_lod_tests(self, asset_name, lod_names, lod_build_settings, mesh_type):
        self.blender.set_addon_property('scene', 'send2ue', 'import_lods', True)

        # TODO: temporary disabling import_groom before groom lods support is added
        self.blender.set_addon_property('scene', 'send2ue', 'import_grooms', False)

        # set the lod build settings
        for key, value in lod_build_settings.items():
            self.blender.set_addon_property(
                'scene',
                'send2ue',
                f'unreal.editor_{mesh_type.lower()}_mesh_library.lod_build_settings.{key}',
                value
            )
        self.move_to_collection(lod_names, 'Export')
        self.send2ue_operation()
        self.assert_mesh_import(asset_name)
        folder_path = self.blender.get_addon_property('scene', 'send2ue', 'unreal_mesh_folder_path')
        asset_path = f'{folder_path}{asset_name}'
        lod_count = self.unreal.get_lod_count(asset_path)
        self.assertEqual(
            lod_count,
            len(lod_names),
            f'The number of lods {len(lod_names)} does not match the number of lods {lod_count} in unreal'
        )

        for index in range(0, lod_count):
            self.log(f'Checking if "{asset_name}" lod{index} build settings match...')
            unreal_build_settings = self.unreal.get_lod_build_settings(asset_path, index)

            for key, value in lod_build_settings.items():
                unreal_value = unreal_build_settings.get(key)
                self.assertEqual(
                    unreal_build_settings.get(key),
                    value,
                    f'The lod build setting "{key}" value "{value}" does not match the unreal value "{unreal_value}"'
                )

    def run_animation_tests(self, objects_and_attributes):
        for object_name, data in objects_and_attributes.items():
            rig_name = data.get('rig')
            animation_names = data.get('animations')
            bones = data.get('bones')
            frames = data.get('frames')
            groom_names = data.get('grooms')
            self.move_to_collection([object_name, rig_name], 'Export')

            self.assert_export_all_actions(animation_names)

            # check that the animations are identical
            for animation_name in animation_names:
                for bone in bones:
                    self.assert_animation_hierarchy(rig_name, animation_name, bone, include_object=True)
                    for frame in frames:
                        self.assert_animation_translation(rig_name, animation_name, bone, frame)

            mesh_folder = '/Game/mesh_test/'
            animation_folder = '/Game/animation_test/'
            groom_folder = '/Game/groom_test/'
            skeleton_path = f'/Game/untitled_category/untitled_asset/{object_name}_Skeleton'
            self.blender.set_addon_property('scene', 'send2ue', 'unreal_mesh_folder_path', mesh_folder)
            self.blender.set_addon_property('scene', 'send2ue', 'unreal_animation_folder_path', animation_folder)
            self.blender.set_addon_property('scene', 'send2ue', 'unreal_groom_folder_path', groom_folder)
            self.blender.set_addon_property('scene', 'send2ue', 'unreal_skeleton_asset_path', skeleton_path)

            self.assert_animation_only_import(object_name, animation_names, groom_names)

            # clear the import area
            self.unreal.delete_directory(mesh_folder)
            self.unreal.delete_directory(animation_folder)

            self.assert_muted_tracks(rig_name, animation_names)

            # clear the import area
            self.unreal.delete_directory(mesh_folder)
            self.unreal.delete_directory(animation_folder)

            self.assert_solo_track(rig_name, animation_names)

    def run_groom_tests(self, meshes_and_particles):
        for mesh_name, particle_names in meshes_and_particles.items():
            particle_hair = particle_names.get('particle_hair')
            particle_emitter = particle_names.get('particle_emitter')
            disabled = particle_names.get('disabled')

            all_particle_names = {
                'enabled': particle_hair + particle_emitter,
                'disabled': disabled
            }

            # NOTE: passing in particle system names here only works because all particle modifiers share the same name
            # as their associated particle systems in the .blend mannequin test file
            self.set_select_particles_visible(mesh_name, all_particle_names)

        self.send2ue_operation()

        for mesh, particle_names in meshes_and_particles.items():
            curves = particle_names.get('curves')
            particle_hair = particle_names.get('particle_hair')
            particle_emitter = particle_names.get('particle_emitter')
            disabled = particle_names.get('disabled')

            for particle in particle_hair + curves:
                self.assert_groom_import(particle, True)

            for particle in particle_emitter + disabled:
                self.assert_groom_import(particle, False)

            self.assert_curves_removal(mesh, curves)

    def run_socket_tests(self, objects_and_sockets):
        for object_name, socket_names in objects_and_sockets.items():
            self.move_to_collection([object_name] + socket_names, 'Export')

            for socket_name in socket_names:
                self.blender.parent_to(socket_name, object_name)

            self.send2ue_operation()
            for socket_name in socket_names:
                self.assert_socket(object_name, socket_name.replace('SOCKET_', ''))

    def run_collision_tests(self, objects_and_collisions):
        for object_and_collisions in objects_and_collisions:
            for object_name, collision_data in object_and_collisions.items():
                simple_count = collision_data.get('simple_count')
                convex_count = collision_data.get('convex_count')
                collision_objects = collision_data.get('objects')

                self.move_to_collection([object_name] + collision_objects, 'Export')
                self.send2ue_operation()
                self.assert_collision(
                    object_name,
                    simple_count=simple_count,
                    convex_count=convex_count
                )
                self.setUp()

    def run_material_tests(self, objects_and_materials):
        for object_name, data in objects_and_materials.items():
            asset_name = data.get('asset')
            materials = data.get('materials')

            # turn on material imports
            self.move_to_collection([object_name], 'Export')
            self.blender.set_addon_property('scene', 'send2ue', 'import_materials_and_textures', True)
            self.send2ue_operation()
            for material_name, material_index in materials.items():
                self.assert_material(asset_name, material_name, material_index, True)

            # reset blender and unreal
            self.tearDown()
            self.setUp()

            # turn off material imports
            self.move_to_collection([object_name], 'Export')
            self.blender.set_addon_property('scene', 'send2ue', 'import_materials_and_textures', False)
            self.send2ue_operation()
            for material_name, material_index in materials.items():
                self.assert_material(asset_name, material_name, material_index, False)

    def run_texture_tests(self, objects_and_textures):
        for object_name, texture_names in objects_and_textures.items():
            self.move_to_collection([object_name], 'Export')
            self.blender.set_addon_property('scene', 'send2ue', 'import_materials_and_textures', True)
            self.send2ue_operation()
            for texture_name in texture_names:
                self.assert_texture(texture_name, True)

            # reset blender and unreal
            self.tearDown()
            self.setUp()

            self.move_to_collection([object_name], 'Export')
            self.blender.set_addon_property('scene', 'send2ue', 'import_materials_and_textures', False)
            self.send2ue_operation()
            for texture_name in texture_names:
                self.assert_texture(texture_name, False)

    def run_auto_stash_active_action_option_tests(self, objects_and_animations):
        self.blender.set_addon_property('scene', 'send2ue', 'export_all_actions', True)
        self.blender.set_addon_property('scene', 'send2ue', 'import_animations', True)
        # turn off auto_stash_active_action
        self.blender.set_addon_property('scene', 'send2ue', 'auto_stash_active_action', False)
        for object_name, data in objects_and_animations.items():
            rig_name = data.get('rig')
            animation_names = data.get('animations')
            self.move_to_collection([object_name, rig_name], 'Export')
            self.tearDown()
            self.send2ue_operation()
            self.assert_mesh_import(object_name)
            for index, animation_name in enumerate(animation_names):
                self.assert_animation_import(animation_name, bool(index))

    def run_export_object_name_as_root_option_tests(self, objects_and_animations):
        self.blender.set_addon_property('scene', 'send2ue', 'export_all_actions', True)
        self.blender.set_addon_property('scene', 'send2ue', 'import_animations', True)
        self.blender.set_addon_property('scene', 'send2ue', 'export_object_name_as_root', False)

        for object_name, data in objects_and_animations.items():
            rig_name = data.get('rig')
            animation_names = data.get('animations')
            bone_names = data.get('bones')
            frames = data.get('frames')
            self.move_to_collection([object_name, rig_name], 'Export')
            self.send2ue_operation()
            self.assert_mesh_import(object_name)
            # check that the animations are identical
            for animation_name in animation_names:
                for bone_name in bone_names:
                    self.assert_animation_hierarchy(rig_name, animation_name, bone_name, include_object=False)
                    for frame in frames:
                        self.assert_animation_translation(rig_name, animation_name, bone_name, frame)

    def run_export_custom_property_fcurves_option_tests(self, objects_and_animations):
        self.blender.set_addon_property('scene', 'send2ue', 'export_all_actions', True)
        self.blender.set_addon_property('scene', 'send2ue', 'import_animations', True)
        self.blender.set_addon_property('scene', 'send2ue', 'export_custom_property_fcurves', True)

        for object_name, data in objects_and_animations.items():
            rig_name = data.get('rig')
            animations = data.get('animations')
            self.move_to_collection([object_name, rig_name], 'Export')
            self.send2ue_operation()
            self.assert_mesh_import(object_name)

            for animation_name, curve_data in animations.items():
                # asserts that the morph targets exist
                self.assert_morph_targets(object_name, list(curve_data.keys()))

                for curve_name, exists in curve_data.items():
                    self.assert_curve(animation_name, curve_name, exists)

    def test_default_send_to_unreal(self):
        """
        Sends a cube mesh with default settings.
        """
        raise NotImplementedError('This test case must be implemented or skipped')

    def test_bulk_send_to_unreal(self):
        """
        Sends multiple cubes to unreal at once.
        """
        raise NotImplementedError('This test case must be implemented or skipped')

    def test_animations(self):
        """
        Sends the mannequin animations to unreal with various options and ensures they are identical.
        """
        raise NotImplementedError('This test case must be implemented or skipped')

    def test_lods(self):
        """
        Sends both cube meshes with lods to unreal.
        https://github.com/EpicGames/BlenderTools/issues/331
        """
        raise NotImplementedError('This test case must be implemented or skipped')

    def test_sockets(self):
        """
        Sends a Cube with sockets to unreal.
        https://github.com/EpicGames/BlenderTools/issues/69
        """
        raise NotImplementedError('This test case must be implemented or skipped')

    def test_collisions(self):
        """
        Sends a Cube with complex collisions to unreal.
        https://github.com/EpicGames/BlenderTools/issues/22
        """
        raise NotImplementedError('This test case must be implemented or skipped')

    def test_materials(self):
        """
        Sends a Cube with materials to unreal.
        """
        raise NotImplementedError('This test case must be implemented or skipped')

    def test_textures(self):
        """
        Sends a Cube with a textured material to unreal.
        https://github.com/EpicGames/BlenderTools/issues/83
        """
        raise NotImplementedError('This test case must be implemented or skipped')

    def test_auto_stash_active_action_option(self):
        """
        Tests not using auto stash active action option.
        """
        raise NotImplementedError('This test case must be implemented or skipped')

    def test_export_object_name_as_root_option(self):
        """
        Tests export object name as root option.
        https://github.com/EpicGames/BlenderTools/issues/121
        """
        raise NotImplementedError('This test case must be implemented or skipped')

    def test_export_custom_property_fcurves_option(self):
        """
        Tests export custom property fcurves option.
        """
        raise NotImplementedError('This test case must be implemented or skipped')

    def test_use_object_origin_option(self):
        """
        Offsets Cube1_LOD0 and tests with the use_object_origin option on and off.
        https://github.com/EpicGames/BlenderTools/issues/223
        """
        raise NotImplementedError('This test case must be implemented or skipped')


class SkipSend2UeTests(unittest.TestCase):
    @unittest.skip
    def test_default_send_to_unreal(self):
        pass

    @unittest.skip
    def test_bulk_send_to_unreal(self):
        pass

    @unittest.skip
    def test_lods(self):
        pass

    @unittest.skip
    def test_sockets(self):
        pass

    @unittest.skip
    def test_collisions(self):
        pass

    @unittest.skip
    def test_materials(self):
        pass

    @unittest.skip
    def test_textures(self):
        pass

    @unittest.skip
    def test_import_asset_operator(self):
        pass

    @unittest.skip
    def test_scene_data_persistence(self):
        pass

    @unittest.skip
    def test_animations(self):
        pass

    @unittest.skip
    def test_grooms(self):
        pass

    @unittest.skip
    def test_auto_stash_active_action_option(self):
        pass

    @unittest.skip
    def test_export_object_name_as_root_option(self):
        pass

    @unittest.skip
    def test_use_object_origin_option(self):
        pass

    @unittest.skip
    def test_export_custom_property_fcurves_option(self):
        pass

    @unittest.skip
    def test_extension(self):
        pass


class BaseUe2RigifyTestCase(BaseTestCase):
    def __init__(self, *args, **kwargs):
        super(BaseUe2RigifyTestCase, self).__init__(*args, **kwargs)
        self.addon_name = 'ue2rigify'

    def setUp(self):
        super(BaseUe2RigifyTestCase, self).setUp()

        # enable the rigify addon
        self.blender.enable_addon('rigify')

    def get_bone_locations(self, rig_name, animation_names, bone_names, frames, control_rig_name=None):
        data = []
        for animation_name in animation_names:
            for bone_name in bone_names:
                for frame in frames:
                    location = self.blender.get_world_bone_translation_for_frame(
                        rig_name,
                        bone_name,
                        animation_name,
                        frame,
                        control_rig_name
                    )
                    data.append(
                        (animation_name, bone_name, frame, location)
                    )
        return data

    def assert_bone_locations(self, rig_name, bones_data1, bones_data2):
        for index, (animation, bone, frame, location1) in enumerate(bones_data1):
            _, _, _, location2 = bones_data2[index]
            self.assertTrue(
                location1 == location2,
                (
                    f'The world location {location1} of bone "{bone}" on "{rig_name}" does not match the world '
                    f'location {location2} of bone "{bone}" at frame {frame} in animation "{animation}".'
                )
            )

    def assert_animation_translation(
        self,
        source_rig_name,
        control_rig_name,
        animation_names,
        bone_names,
        frames,
        ik_fk_switch=None
    ):
        source_mode = self.get_bone_locations(source_rig_name, animation_names, bone_names, frames)
        self.blender.run_addon_operator(self.addon_name, 'switch_modes', [], {'mode': 'CONTROL'})
        control_mode = self.get_bone_locations(source_rig_name, animation_names, bone_names, frames, control_rig_name)
        self.log(
            f'Checking "{source_rig_name}" world location of bones after switch to control mode...'
        )
        # check that the bone locations still match after the mode change
        self.assert_bone_locations(source_rig_name, source_mode, control_mode)

        # turn on iks
        if ik_fk_switch:
            self.log(f'Turning on IK/FK switch for {list(ik_fk_switch.values())}...')
            self.blender.set_rigify_ik_fk(control_rig_name, ik_fk_switch, 0.0)
            control_mode = self.get_bone_locations(
                source_rig_name,
                animation_names,
                bone_names,
                frames,
                control_rig_name
            )

        self.blender.run_addon_operator(self.addon_name, 'bake_from_rig_to_rig')
        post_bake = self.get_bone_locations(source_rig_name, animation_names, bone_names, frames)

        self.log(
            f'Checking "{source_rig_name}" to see the bones are in the same world location after the bake...'
        )
        # check that the bone locations still match after the bake
        self.assert_bone_locations(source_rig_name, control_mode, post_bake)

    def run_modes_tests(self, rigs_and_modes):
        for rig_name, data in rigs_and_modes.items():
            template = data.get('template')
            modes = data.get('modes')

            self.blender.set_addon_property('scene', 'ue2rigify', 'source_rig', rig_name, 'object')
            self.blender.set_addon_property('scene', 'ue2rigify', 'selected_rig_template', template)
            for mode in modes:
                self.log(f'switching "{rig_name}" to "{mode}" mode...')
                self.blender.set_addon_property('scene', self.addon_name, 'selected_mode', mode)
                previous_mode = self.blender.get_addon_property('scene', 'ue2rigify', 'previous_mode')
                self.assertEqual(
                    mode,
                    previous_mode,
                    f'The selected mode "{previous_mode}" failed to switch to "{mode}" on "{rig_name}".'
                )

    def run_new_template_tests(self, rigs_and_templates):
        for rig_name, data in rigs_and_templates.items():
            new_template_name = data.get('new_template_name')
            starter_template_name = data.get('starter_template_name')
            fk_to_source = data.get('fk_to_source')
            source_to_deform = data.get('source_to_deform')

            self.blender.set_addon_property('scene', self.addon_name, 'source_rig', rig_name, 'object')
            self.blender.set_addon_property('scene', self.addon_name, 'selected_mode', 'SOURCE')
            self.blender.set_addon_property('scene', self.addon_name, 'selected_rig_template', 'create_new')
            self.blender.set_addon_property(
                'scene',
                self.addon_name,
                'selected_starter_metarig_template',
                starter_template_name
            )
            self.blender.set_addon_property('scene', 'ue2rigify', 'new_template_name', new_template_name)

            self.log(f'Saving new template "{new_template_name}"...')
            self.blender.run_addon_operator(self.addon_name, 'save_metarig')

            # create some fk to source nodes
            self.blender.set_addon_property('scene', self.addon_name, 'selected_mode', 'FK_TO_SOURCE')
            for fk_bone_name, source_bone_name in fk_to_source.items():
                self.blender.select_bones('rig', [fk_bone_name])
                self.blender.select_bones(rig_name, [source_bone_name])
                self.blender.run_addon_operator(self.addon_name, 'create_link_from_selected_bones')

            # create some source to deform nodes
            self.blender.set_addon_property('scene', self.addon_name, 'selected_mode', 'SOURCE_TO_DEFORM')
            for source_bone_name, deform_bone_name in source_to_deform.items():
                self.blender.select_bones(rig_name, [source_bone_name])
                self.blender.select_bones('rig', [deform_bone_name])
                self.blender.run_addon_operator(self.addon_name, 'create_link_from_selected_bones')

            saved_node_data = self.blender.get_addon_property('scene', self.addon_name, 'saved_node_data')
            saved_links_data = self.blender.get_addon_property('scene', self.addon_name, 'saved_links_data')
            saved_metarig_data = self.blender.get_addon_property('scene', self.addon_name, 'saved_metarig_data')

            # check that each of the template files exist
            for template_file_path in [saved_metarig_data, saved_node_data, saved_links_data]:
                self.log(f'Checking that "{template_file_path}" exists...')
                self.assertTrue(
                    self.blender.path_exists(template_file_path),
                    f'"{template_file_path}" does not exist!'
                )

            # remove the template
            self.log(f'Removing template "{new_template_name}"...')
            self.blender.run_addon_operator(
                self.addon_name,
                'remove_rig_template',
                None,
                {'template': new_template_name}
            )

    def run_baking_tests(self, rigs_and_modes):
        for rig_name, data in rigs_and_modes.items():
            template = data.get('template')
            control_rig_name = data.get('control_rig')
            animation_names = data.get('animations')
            bone_names = data.get('bones')
            frames = data.get('frames')
            ik_fk_switch = data.get('ik_fk_switch')

            self.blender.set_addon_property('scene', self.addon_name, 'source_rig', rig_name, 'object')
            self.blender.set_addon_property('scene', self.addon_name, 'selected_rig_template', template)
            self.blender.set_addon_property('scene', self.addon_name, 'overwrite_control_animations', True)

            self.assert_animation_translation(rig_name, control_rig_name, animation_names, bone_names, frames)
            # self.setUp()
            self.assert_animation_translation(
                rig_name,
                control_rig_name,
                animation_names,
                bone_names,
                frames,
                ik_fk_switch
            )

    def run_template_sharing_tests(self, rigs_and_templates):
        for rig_name, data in rigs_and_templates.items():
            template_name = data.get('template')

            self.blender.set_addon_property('scene', self.addon_name, 'source_rig', rig_name, 'object')
            template_file_name = f'{template_name}_test.zip'
            file_path = os.path.join(self.test_folder, 'test_files', 'data', template_file_name)
            # make the path a linux path if in the test environment
            if self.test_environment:
                file_path = os.path.normpath(file_path).replace(os.path.sep, '/')

            # export the template
            self.log(f'Exporting template "{template_name}"...')
            self.blender.set_addon_property('scene', self.addon_name, 'selected_export_template', template_name)
            self.blender.run_addon_operator(self.addon_name, 'export_rig_template', None, {'filepath': file_path})

            # import the template
            self.log(f'Importing template "{template_name}"...')
            self.blender.run_addon_operator(self.addon_name, 'import_rig_template', None, {'filepath': file_path})

            base_path = [
                self.ue2rigify.constants.ToolInfo.NAME.value,
                'resources',
                'rig_templates',
                f'{template_name}_test'
            ]

            template_file_paths = [
                base_path + ['metarig.py'],
                base_path + ['source_to_deform_links.json'],
                base_path + ['source_to_deform_nodes.json'],
                base_path + ['fk_to_source_nodes.json'],
                base_path + ['fk_to_source_links.json']
            ]

            for template_file_path in template_file_paths:
                self.assertTrue(
                    self.blender.has_temp_file(template_file_path),
                    f'The template file "{os.path.join(*template_file_path)}" does not exist when it should.'
                )

            # remove the template
            self.log(f'Removing template "{template_name}"...')
            self.blender.run_addon_operator(
                self.addon_name,
                'remove_rig_template',
                None,
                {'template': f'{template_name}_test'}
            )
            for template_file_path in template_file_paths:
                self.assertFalse(
                    self.blender.has_temp_file(template_file_path),
                    f'The template file "{os.path.join(*template_file_path)}" exists when it should have been removed.'
                )

    def test_modes(self):
        """
        Switches through each mode.
        """
        raise NotImplementedError('This test case must be implemented or skipped')

    def test_new_template(self):
        """
        Tests creating a new template.
        https://github.com/EpicGames/BlenderTools/issues/233
        """
        raise NotImplementedError('This test case must be implemented or skipped')

    def test_baking(self):
        """
        related issue:
        This tests that baking the bone transforms is correct.
        https://github.com/EpicGames/BlenderTools/issues/238
        """
        raise NotImplementedError('This test case must be implemented or skipped')
