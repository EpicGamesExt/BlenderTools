# Copyright Epic Games, Inc. All Rights Reserved.
import os
import bpy
import unittest


class Ue2RigifyTemplates(unittest.TestCase):
    """
    related issue:
    https://github.com/EpicGames/BlenderTools/issues/233
    This tests that the tools template system
    """

    @staticmethod
    def get_rig_templates_path():
        """
        This is a helper method that returns the path to the addons rig template directory.

        :return str: The full path to the addons rig template directory.
        """
        addons = bpy.utils.user_resource('SCRIPTS', 'addons')
        return os.path.join(
            addons,
            'ue2rigify',
            'resources',
            'rig_templates'
        )

    def setUp(self):
        # load in the file you will run tests on
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'skeletal_meshes.blend'))

        # disable the send2ue addon
        bpy.ops.preferences.addon_disable(module='send2ue')

        # enable the rigify addon
        bpy.ops.preferences.addon_enable(module='rigify')

        # enable the ue2rigify addon
        bpy.ops.preferences.addon_enable(module='ue2rigify')

    def tearDown(self):
        # enable the send2ue addon
        bpy.ops.preferences.addon_enable(module='send2ue')

        # restore blend file to the default test file
        bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ['BLENDS'], 'default_startup.blend'))

    def test_create_new_template(self):
        """
        This method creates a new template and checks that it saved correctly.
        """
        # all the template files
        template_files = [
            # 'fk_to_source_links.json',
            # 'fk_to_source_nodes.json',
            # 'source_to_deform_links.json',
            # 'source_to_deform_nodes.json',
            'metarig.py',
        ]

        if bpy.app.version[0] <= 2 and bpy.app.version[1] < 92:
            template_files.append('metarig_constraints.json')

        properties = bpy.context.window_manager.ue2rigify

        # un freeze the rig
        bpy.ops.ue2rigify.un_freeze_rig()

        # set the source rig object
        properties.source_rig_name = 'root'

        # switch to source mode
        bpy.ops.ue2rigify.switch_modes(mode='SOURCE')

        # create a new template
        properties.selected_rig_template = 'create_new'

        # select the basic human starter template
        properties.selected_starter_metarig_template = 'bpy.ops.object.armature_basic_human_metarig_add()'

        properties.new_template_name = 'Basic Human Test'

        # save the new metarig
        bpy.ops.ue2rigify.save_metarig()

        # check that each of the template files exist
        for template_file in template_files:
            file_path = os.path.join(self.get_rig_templates_path(), 'basic_human_test', template_file)
            self.assertTrue(os.path.exists(file_path), msg=f'"{file_path}" does not exist!')
