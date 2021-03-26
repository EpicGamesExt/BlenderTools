# Copyright Epic Games, Inc. All Rights Reserved.
import os
import bpy
import json
import unittest
from mathutils import Color, Euler, Matrix, Quaternion, Vector


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

    @staticmethod
    def get_matrix_data(matrix_object):
        """
        This function destructures a matrix object into a list of lists.

        :param object matrix_object:
        :return list: A list of lists that represents a matrix.
        """
        matrix_data = []
        for column in matrix_object.col:
            col_values = []
            for col_value in column:
                col_values.append(col_value)

            matrix_data.append(col_values)

        return matrix_data

    @staticmethod
    def get_array_data(array_object):
        """
        This function destructures any of the array object data types into a list.

        :param object array_object: A object array such as Color, Euler, Quaternion, Vector.
        :return list: A list of values.
        """
        array_data = []
        for value in array_object:
            array_data.append(value)

        return array_data

    @staticmethod
    def get_property_collections_data(collections):
        """
        This function goes through each of the givens collections and return their data as a list of dictionaries.

        :param list collections: A list a property groups.
        :return list: A list of dictionaries that contains the given property group values.
        """
        collections_data = []
        for collection in collections:
            property_collection = {}
            for collection_attribute in dir(collection):
                collection_value = getattr(collection, collection_attribute)
                if collection_value is not None and not collection_attribute.startswith('__'):
                    if type(collection_value) in [str, bool, int, float]:
                        property_collection[collection_attribute] = collection_value

                    if type(collection_value) == bpy.types.Object:
                        property_collection[collection_attribute] = collection_value.name
            collections_data.append(property_collection)

        return collections_data

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
        if bpy.app.version[0] <= 2 and bpy.app.version[1] < 92:
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

            # un freeze the rig
            bpy.ops.ue2rigify.un_freeze_rig()

            # switch to metarig mode
            bpy.ops.ue2rigify.switch_modes(mode='METARIG')

            # get the metarig and source rig
            metarig_object = bpy.data.objects['metarig']
            source_object = bpy.data.objects['root']

            # create every type of constraint on the rigs bones
            for index, constraint_type in enumerate(constraint_types):
                bone = metarig_object.pose.bones[index]
                constraint = bone.constraints.new(constraint_type)

                # if it is an armature constraint create a target
                if constraint_type == 'ARMATURE':
                    constraint.targets.new()
                    constraint.targets[0].target = source_object
                    constraint.targets[0].subtarget = 'ball_l'

                if hasattr(constraint_types, 'target'):
                    constraint.target = source_object

                if hasattr(constraint_types, 'subtarget'):
                    constraint.subtarget = 'ball_l'

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
                                    value = self.get_matrix_data(value)

                                if attribute == 'target':
                                    value = value.name

                                if type(value) in [Color, Euler, Quaternion, Vector]:
                                    value = self.get_array_data(value)

                                if type(value) == bpy.types.bpy_prop_collection:
                                    value = self.get_property_collections_data(value)

                                saved_value = constraint_data.get(attribute)
                                if saved_value:
                                    self.assertEqual(value, saved_value)
