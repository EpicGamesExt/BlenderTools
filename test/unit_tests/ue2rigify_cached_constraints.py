# Copyright Epic Games, Inc. All Rights Reserved.
import os
import bpy
import json
import unittest
from mathutils import Matrix


class Ue2RigifyCachedConstraintsTestCases(unittest.TestCase):
    """
    related issue:
    https://github.com/EpicGames/BlenderTools/issues/218
    This tests that all the constraints are caching correctly in the templates.
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

    def get_saved_metarig_constraints(self):
        """
        This is a helper method that gets the saved metarig constraints.

        :return dict: A dictionary of saved constraints.
        """
        saved_constraints_file_path = os.path.join(
            self.get_rig_templates_path(),
            'unreal_mannequin',
            'metarig_constraints.json'
        )
        if os.path.exists(saved_constraints_file_path):
            saved_constraints_file = open(saved_constraints_file_path)
            return json.load(saved_constraints_file)
        else:
            return {}

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

    def test_all_constraint_types(self):
        """
        This method goes through every constraint type and creates it on the metarig and checks if they saved correctly.
        """
        # all the currently available constraints in blender that will be tested
        constraint_types = [
            'CAMERA_SOLVER',
            'FOLLOW_TRACK',
            'OBJECT_SOLVER',
            'COPY_LOCATION',
            'COPY_ROTATION',
            'COPY_SCALE',
            'COPY_TRANSFORMS',
            'LIMIT_DISTANCE',
            'LIMIT_LOCATION',
            'LIMIT_ROTATION',
            'LIMIT_SCALE',
            'MAINTAIN_VOLUME',
            'TRANSFORM',
            'TRANSFORM_CACHE',
            'CLAMP_TO',
            'DAMPED_TRACK',
            'IK',
            'LOCKED_TRACK',
            'SPLINE_IK',
            'STRETCH_TO',
            'TRACK_TO',
            'ACTION',
            'ARMATURE',
            'CHILD_OF',
            'FLOOR',
            'FOLLOW_PATH',
            'PIVOT',
            'SHRINKWRAP'
        ]

        # set the source rig object
        bpy.context.window_manager.ue2rigify.source_rig_name = 'root'

        # switch to metarig mode
        bpy.ops.ue2rigify.switch_modes(mode='METARIG')

        # get the metarig and source rig
        metarig_object = bpy.data.objects['metarig']
        source_object = bpy.data.objects['root']

        # create every type of constraint on the rigs bones
        for index, constraint_type in enumerate(constraint_types):
            bone = metarig_object.pose.bones[index]
            constraint = bone.constraints.new(constraint_type)

            if hasattr(constraint_types, 'target'):
                constraint.target = source_object

            if hasattr(constraint_types, 'subtarget'):
                constraint.target = 'ball_l'

        # switch to source mode
        bpy.ops.ue2rigify.switch_modes(mode='SOURCE')

        # switch to metarig mode
        bpy.ops.ue2rigify.switch_modes(mode='METARIG')
        metarig_object = bpy.data.objects['metarig']

        for bone_name, constraints_data in self.get_saved_metarig_constraints().items():
            print(bone_name, constraints_data)
            bone = metarig_object.pose.bones[bone_name]
            for constraint_data in constraints_data:
                constraint = bone.constraints.get(constraint_data['name'])
                for attribute in dir(constraint):
                    value = getattr(constraint, attribute)
                    if value is not None and not attribute.startswith('__'):
                        # dont save the attributes that are a type of constraint object
                        if not type(value).__name__.endswith('Constraint'):
                            # destructure the matrix object into a list of lists
                            if type(value) == Matrix:
                                destructured_matrix = []
                                for col in value.col:
                                    col_values = []
                                    for col_value in col:
                                        col_values.append(col_value)

                                    destructured_matrix.append(col_values)

                                value = destructured_matrix

                            if attribute == 'target':
                                value = value.name

                            # destructure other data types
                            if type(value) not in [str, bool, int, float]:
                                data = []
                                for sub_value in value:
                                    data.append(sub_value)
                                value = data

                            saved_value = constraint_data.get(attribute)
                            if saved_value:
                                self.assertEqual(value, saved_value)
