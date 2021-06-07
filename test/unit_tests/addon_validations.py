# Copyright Epic Games, Inc. All Rights Reserved.
import bpy
import unittest


class AddonValidationTestCases(unittest.TestCase):
    """
    related issue:
    https://github.com/EpicGames/BlenderTools
    ^ This is a core addon feature, but if this feature was created based off an issue, a link to the issue
    should be left is the docstring.
    """

    def __init__(self, *args, **kwargs):
        super(AddonValidationTestCases, self).__init__(*args, **kwargs)

        # this is the list of send2ue properties not to validate
        self.send2ue_excluded_properties = [
            'bl_idname',
            'error_message',
            'error_message_details',
            'use_ue2rigify',
            'show_fbx_settings',
            'incorrect_disk_mesh_folder_path',
            'incorrect_disk_animation_folder_path',
            'axis_forward',
            'axis_up',
            'primary_bone_axis',
            'secondary_bone_axis',
            'use_metadata',
            'mesh_folder_untitled_blend_file',
            'animation_folder_untitled_blend_file',
            'incorrect_static_mesh_name_affix',
            'incorrect_texture_name_affix',
            'incorrect_material_name_affix',
            'incorrect_skeletal_mesh_name_affix',
            'incorrect_animation_sequence_name_affix',
            'incorrect_unreal_mesh_folder_path',
            'incorrect_unreal_animation_folder_path',
            'incorrect_unreal_skeleton_path',
            'sub_folder_path',
            'show_animation_settings',
            'show_name_affix_settings',
        ]

        # this is the list of ue2rigify properties not to validate
        self.ue2rigify_excluded_properties = [
            'saved_metarig_data',
            'saved_links_data',
            'saved_node_data',
            'previous_mode',
            'source_rig_name',
            'check_node_tree_for_updates',
            'current_nodes_and_links',
            'freeze_rig'
        ]

    def check_addon_property_descriptions(self, properties, excluded_properties):
        """
        This method checks that the given addon property descriptions are unique and not empty.

        :param object properties: The property group object that contains all of the addon properties.
        :param list excluded_properties: A list of property names to exclude from the validation process.
        """
        descriptions = {}
        for key, value in properties.bl_rna.properties.items():

            if key not in excluded_properties:
                # checks if the description is an empty string
                self.assertTrue(value.description, f'"{key}" has a blank description!')

                # checks if the description is unique
                self.assertTrue(
                    value.description not in descriptions.keys(),
                    f'"{key}" has the same description as "{descriptions.get(value.description)}"!'
                )

                # save each unique description
                descriptions[value.description] = key

    def check_addon_property_names(self, properties, excluded_properties):
        """
        This method checks that the given addon property names are unique and not empty.

        :param object properties: The property group object that contains all of the addon properties.
        :param list excluded_properties: A list of property names to exclude from the validation process.
        """
        names = {}
        for key, value in properties.bl_rna.properties.items():

            if key not in excluded_properties:
                # checks if the name is an empty string
                self.assertTrue(value.name, f'"{key}" has a blank name!')

                # checks if the name is unique
                self.assertTrue(
                    value.name not in names.keys(),
                    f'"{key}" has the same name as "{names.get(value.description)}"!'
                )

                # save each unique name
                names[value.description] = key

    def setUp(self):
        """
        This method is called before any of the methods in this unit test are run.
        """
        # reload all scripts
        bpy.ops.script.reload()

    def test_is_send2ue_enabled(self):
        """
        This method checks if send2ue is enabled.
        """
        self.assertTrue(bool(bpy.context.preferences.addons.get('send2ue')))

    def test_is_ue2rigify_enabled(self):
        """
        This method checks if ue2rigify is enabled.
        """
        self.assertTrue(bool(bpy.context.preferences.addons.get('ue2rigify')))

    def test_send2ue_names(self):
        """
        This method checks if all the send2ue property names are unique and not empty.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences
        self.check_addon_property_names(properties, self.send2ue_excluded_properties)

    def test_ue2rigify_names(self):
        """
        This method checks if all the ue2rigify property names are unique and not empty.
        """
        properties = bpy.context.window_manager.ue2rigify
        self.check_addon_property_names(properties, self.ue2rigify_excluded_properties)

    def test_send2ue_descriptions(self):
        """
        This method checks if all the send2ue property descriptions are unique and not empty.
        """
        properties = bpy.context.preferences.addons['send2ue'].preferences
        self.check_addon_property_descriptions(properties, self.send2ue_excluded_properties)

    def test_ue2rigify_descriptions(self):
        """
        This method checks if all the ue2rigify property descriptions are unique and not empty.
        """
        properties = bpy.context.window_manager.ue2rigify
        self.check_addon_property_descriptions(properties, self.ue2rigify_excluded_properties)
