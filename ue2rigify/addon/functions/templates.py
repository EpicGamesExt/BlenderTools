# Copyright Epic Games, Inc. All Rights Reserved.

import os
import re
import bpy
import json
import shutil
from mathutils import Color, Euler, Matrix, Quaternion, Vector

from . import scene
from . import utilities
from ..settings.tool_tips import *

_result_reference_get_starter_metarig_templates = []
_result_reference_populate_templates_dropdown = []
_result_reference_get_modes = []
_result_reference_get_rig_templates = []


# -------------- functions that handle the rig templating --------------
def get_rig_templates_path():
    """
    This function returns the path to the addons rig template directory.

    :return str: The full path to the addons rig template directory.
    """
    addons = bpy.utils.user_resource('SCRIPTS', 'addons')
    return os.path.join(addons, __package__.split('.')[0], 'resources', 'rig_templates')


def get_saved_node_data(properties):
    """
    This function reads from disk a list of dictionaries that are saved node attributes.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return list: A list of dictionaries that contain node attributes.
    """
    if os.path.exists(properties.saved_node_data):
        saved_node_data_file = open(properties.saved_node_data)
        saved_node_data = json.load(saved_node_data_file)
        saved_node_data_file.close()
        return saved_node_data
    else:
        return None


def get_saved_links_data(properties, reverse=False):
    """
    This function reads from disk a list of dictionaries that are saved link attributes.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :param bool reverse: If true it flips the from and to nodes and sockets
    :return list: A list of dictionaries that contains link attributes.
    """
    if os.path.exists(properties.saved_links_data):
        saved_links_file = open(properties.saved_links_data)
        saved_links_data = json.load(saved_links_file)
        saved_links_file.close()

        if reverse:
            reversed_saved_links_data = []
            for socket_link in saved_links_data:
                reversed_socket_link = {
                    'from_node': socket_link['to_node'],
                    'to_node': socket_link['from_node'],
                    'to_socket': socket_link['from_socket'],
                    'from_socket': socket_link['to_socket']
                }
                reversed_saved_links_data.append(reversed_socket_link)

            saved_links_data = reversed_saved_links_data

        return saved_links_data
    else:
        return []


def get_saved_constraints_data(mode, properties):
    """
    This function reads from disk a list of dictionaries that are saved constraints on the rig.

    :param str mode: The mode to get the saved constraints from.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    saved_constraints_data = {}
    constraints_path = get_template_file_path(f'{mode.lower()}_constraints.json', properties)
    if os.path.exists(constraints_path):
        saved_constraints_file = open(constraints_path)
        saved_constraints_data = json.load(saved_constraints_file)
        saved_constraints_file.close()

    return saved_constraints_data


def get_constraints_data(rig_object):
    """
    This function reads the constraints on the bones of the given rig object.

    :param object rig_object: An object of type rig.
    :return dict: A dictionary of constraint attributes and values.
    """
    constraints_data = {}
    if rig_object:

        for bone in rig_object.pose.bones:
            constraints_data[bone.name] = []
            for constraint in bone.constraints:

                constraint_attributes = {}
                # save all the constraint attributes
                for attribute in dir(constraint):
                    value = getattr(constraint, attribute)
                    if value is not None and not attribute.startswith('__'):
                        # save all the basic types
                        if type(value) in [str, bool, int, float]:
                            constraint_attributes[attribute] = value

                        # save all the mathutils data types in a format that json excepts
                        if type(value) in [Color, Euler, Quaternion, Vector]:
                            constraint_attributes[attribute] = utilities.get_array_data(value)

                        # save objects as their name values
                        if type(value) == bpy.types.Object:
                            constraint_attributes[attribute] = value.name

                        # save a property collection into json
                        if type(value) == bpy.types.bpy_prop_collection:
                            constraint_attributes[attribute] = utilities.get_property_collections_data(value)

                        # save all the matrix data types into a format that json excepts
                        if type(value) == Matrix:
                            constraint_attributes[attribute] = utilities.get_matrix_data(value)

                constraints_data[bone.name].append(constraint_attributes)

    return constraints_data


def get_metarig_data(properties):
    """
    This function encodes the metarig object to a python string.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return object: A blender text object.
    """
    metarig_object = bpy.data.objects.get(properties.meta_rig_name)
    if metarig_object:

        utilities.operator_on_object_in_mode(
            lambda: bpy.ops.armature.rigify_encode_metarig(),
            metarig_object,
            'EDIT'
        )

        metarig_text_object = bpy.data.texts.get(os.path.basename(properties.saved_metarig_data))

        if metarig_text_object:
            return metarig_text_object.as_string()

    return None


def get_starter_metarig_templates(self=None, context=None):
    """
    This function gets the enumeration for the starter metarig template selection.

    :param object self: This is a reference to the class this functions in appended to.
    :param object context: The context of the object this function is appended to.
    :return list: A list of tuples that define the starter metarig template enumeration.
    """
    icon = 'OUTLINER_OB_ARMATURE'
    return [
        ('bpy.ops.object.armature_human_metarig_add()', 'Human', starter_metarig_tool_tip, icon, 0),
        ('bpy.ops.object.armature_basic_human_metarig_add()', 'Basic Human', starter_metarig_tool_tip, icon, 1),
        ('bpy.ops.object.armature_basic_quadruped_metarig_add()', 'Basic Quadruped', starter_metarig_tool_tip, icon, 2),
        ('bpy.ops.object.armature_bird_metarig_add()', 'Bird', starter_metarig_tool_tip, icon, 3),
        ('bpy.ops.object.armature_cat_metarig_add()', 'Cat', starter_metarig_tool_tip, icon, 4),
        ('bpy.ops.object.armature_horse_metarig_add()', 'Horse', starter_metarig_tool_tip, icon, 5),
        ('bpy.ops.object.armature_shark_metarig_add()', 'Shark', starter_metarig_tool_tip, icon, 6),
        ('bpy.ops.object.armature_wolf_metarig_add()', 'Wolf', starter_metarig_tool_tip, icon, 7),
    ]


def get_rig_templates(self=None, context=None):
    """
    This function gets the enumeration for the rig template selection.

    :param object self: This is a reference to the class this functions in appended to.
    :param object context: The context of the object this function is appended to.
    :return list: A list of tuples that define the rig template enumeration.
    """
    rig_templates = []
    rig_template_directories = next(os.walk(get_rig_templates_path()))[1]

    for index, rig_template in enumerate(rig_template_directories):
        rig_templates.append((
            rig_template,
            utilities.set_to_title(rig_template),
            template_tool_tip.format(template_name=utilities.set_to_title(rig_template)),
            'OUTLINER_OB_ARMATURE',
            index
        ))
    return rig_templates


def get_template_file_path(template_file_name, properties):
    """
    This function get the the full path to a template file based on the provided template file name.

    :param str template_file_name: The name of the template file.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return str: The full path to a template file.
    """
    template_name = properties.selected_rig_template

    # assign the new template name
    if properties.selected_rig_template == 'create_new':
        template_name = re.sub(r'\W+', '_', properties.new_template_name).lower()

    return os.path.join(
        properties.rig_templates_path,
        template_name,
        template_file_name
    )


def set_constraints_data(rig_object, properties):
    """
    This function gets the constraints from the template and creates them on the given rig object.

    :param object rig_object: An object of type rig.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    constraints_data = get_saved_constraints_data(properties.metarig_mode, properties)

    if rig_object:
        for bone_name, constraints_data in constraints_data.items():
            if constraints_data:
                bone = rig_object.pose.bones.get(bone_name)

                for constraint_data in constraints_data:
                    # create the constraint
                    constraint_type = constraint_data.pop('type')
                    constraint = bone.constraints.new(constraint_type)

                    # set the constraints attributes
                    for attribute, value in constraint_data.items():
                        current_value = getattr(constraint, attribute)
                        if type(current_value) == bpy.types.bpy_prop_collection:
                            utilities.set_collection(current_value, value)
                        else:
                            utilities.set_property_group_value(constraint, attribute, value)


def set_template_files(properties, mode_override=None):
    """
    This function sets the correct template file paths based on the mode the addon is in.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :param str mode_override: This is an optional parameter that can be used to override the addon's current mode to
    get the desired template path.
    """
    mode = properties.previous_mode.lower()

    if mode_override:
        mode = mode_override.lower()

    properties.saved_metarig_data = get_template_file_path(f'{properties.meta_rig_name}.py', properties)
    properties.saved_links_data = get_template_file_path(f'{mode}_links.json', properties)
    properties.saved_node_data = get_template_file_path(f'{mode}_nodes.json', properties)


def set_template(self=None, context=None):
    """
    This function is called every time a new template is selected. If create new is selected it switch to edit metarig
    mode, but if anything else is selected it defaults to source mode.

    :param object self: This is a reference to the class this functions in appended to.
    :param object context: The context of the object this function is appended to.
    """
    properties = bpy.context.window_manager.ue2rigify

    if hasattr(bpy.context, 'scene'):
        if properties.selected_rig_template == 'create_new':
            properties.selected_mode = properties.metarig_mode
        else:
            properties.selected_mode = properties.source_mode


@bpy.app.handlers.persistent
def set_default_rig_template(*args):
    """
    This function sets the default rig template every time a new file loads and on the first dependency graph update
    right after the addon is registered.

    :param args: This soaks up the extra arguments for the app handler.
    """
    properties = bpy.context.window_manager.ue2rigify
    properties.selected_rig_template = properties.default_template

    if set_default_rig_template in bpy.app.handlers.depsgraph_update_pre:
        bpy.app.handlers.depsgraph_update_pre.remove(set_default_rig_template)


def remove_template_folder(properties):
    """
    This function removes the active template from the addon's rig templates folder.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    # switch back to source mode
    properties.selected_mode = properties.source_mode

    # delete the selected rig template folder
    selected_template_path = os.path.join(properties.rig_templates_path, properties.selected_rig_template)
    try:
        original_umask = os.umask(0)
        if os.path.exists(selected_template_path):
            os.chmod(selected_template_path, 0o777)
        shutil.rmtree(selected_template_path)
    finally:
        os.umask(original_umask)

    # set the selected rig template to the default
    properties.selected_rig_template = properties.default_template


def create_template_folder(template_name, properties):
    """
    This function creates a new template folder in the addon's rig templates folder.

    :param str template_name: The name of the template folder to create.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    # remove non alpha numeric characters
    template_name = re.sub(r'\W+', '_', template_name.strip()).lower()

    # create the template folder
    template_path = os.path.join(properties.rig_templates_path, template_name)
    if not os.path.exists(template_path):
        try:
            original_umask = os.umask(0)
            os.makedirs(template_path, 0o777)
        finally:
            os.umask(original_umask)

    # keep checking the os file system till the new folder exists
    while not os.path.exists(template_path):
        pass

    return template_path


def populate_templates_dropdown(self=None, context=None):
    """
    This function is called every time a the template dropdown is interacted with. It lists all the templates in the
    rig_templates folder.

    :param object self: This is a reference to the class this functions in appended to.
    :param object context: The context of the object this function is appended to.
    """
    rig_templates = get_rig_templates()
    rig_templates.append(('create_new', 'Create New', create_template_tool_tip, 'ADD', len(rig_templates)))
    return rig_templates


def save_text_file(data, file_path):
    """
    This function saves text data to a file provided a full file path.

    :param str data: A text string.
    :param str file_path: The full file path to where the file will be saved.
    """
    if '.py' in os.path.basename(file_path):
        try:
            original_umask = os.umask(0)
            if os.path.exists(file_path):
                os.chmod(file_path, 0o777)
            file = open(file_path, 'w+')
        finally:
            os.umask(original_umask)
        file.write(data)
        file.close()


def save_json_file(data, file_path):
    """
    This function saves json data to a file provided a full file path.

    :param dict data: A dictionary to be saved as json.
    :param str file_path: The full file path to where the file will be saved.
    """
    if '.json' in os.path.basename(file_path):
        try:
            original_umask = os.umask(0)
            if os.path.exists(file_path):
                os.chmod(file_path, 0o777)
            file = open(file_path, 'w+')
        finally:
            os.umask(original_umask)
        json.dump(data, file, indent=1)
        file.close()


def save_constraints(constraints_data, properties):
    """
    This function writes the given rig objects constraints to a file on disk.

    :param dict constraints_data: A dictionary of saved rig constraints.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    saved_constraints_path = get_template_file_path(f'{properties.previous_mode.lower()}_constraints.json', properties)
    save_json_file(constraints_data, saved_constraints_path)


# TODO move to a shared location and define as a generic zip import
def import_zip(zip_file_path, properties):
    """
    This function gets a zip folder and unpacks it into the rig templates folder.

    :param str zip_file_path: The full file path to where the zip file is located.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    # get the template name and path from the zip file
    template_name = os.path.basename(zip_file_path).replace('.zip', '')
    template_folder_path = os.path.join(properties.rig_templates_path, template_name)

    # create the template folder
    create_template_folder(template_name, properties)

    # unpack the zip file into the new template folder
    shutil.unpack_archive(zip_file_path, template_folder_path, 'zip')


# TODO move to a shared location and define as a generic zip export
def export_zip(zip_file_path, properties):
    """
    This function packs the selected export template into a zip folder, and saves it to the provided path on disk.

    :param str zip_file_path: The full file path to where the zip file will be saved on disk.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    # remove .zip extension if it exists
    no_extension_file_path = zip_file_path.replace('.zip', '')

    # zip up the folder and save it to the given path
    template_folder_path = os.path.join(properties.rig_templates_path, properties.selected_export_template)
    shutil.make_archive(no_extension_file_path, 'zip', template_folder_path)

#
# Dynamic EnumProperty item list workaround:
# https://docs.blender.org/api/current/bpy.props.html?highlight=bpy%20props%20enumproperty#bpy.props.EnumProperty
#
#   There is a known bug with using a callback, Python must keep a reference to
#   the strings returned by the callback or Blender will misbehave or even crash.
#   For more information, see:
#


def safe_get_starter_metarig_templates(self, context):
    """
    This function is an EnumProperty safe wrapper for get_starter_metarig_templates.

    :param object self: This is a reference to the class this functions in appended to.
    :param object context: The context of the object this function is appended to.
    :return list: Result of get_starter_metarig_templates.
    """
    items = get_starter_metarig_templates()
    global _result_reference_get_starter_metarig_templates
    _result_reference_get_starter_metarig_templates = items
    return items


def safe_populate_templates_dropdown(self, context):
    """
    This function is an EnumProperty safe wrapper for populate_templates_dropdown.

    :param object self: This is a reference to the class this functions in appended to.
    :param object context: The context of the object this function is appended to.
    :return list: Result of populate_templates_dropdown.
    """
    items = populate_templates_dropdown()
    global _result_reference_populate_templates_dropdown
    _result_reference_populate_templates_dropdown = items
    return items


def safe_get_modes(self, context):
    """
    This function is an EnumProperty safe wrapper for scene.get_modes.

    :param object self: This is a reference to the class this functions in appended to.
    :param object context: The context of the object this function is appended to.
    :return list: Result of scene.get_modes.
    """
    items = scene.get_modes()
    global _result_reference_get_modes
    _result_reference_get_modes = items
    return items


def safe_get_rig_templates(self, context):
    """
    This function is an EnumProperty safe wrapper for get_rig_templates.

    :param object self: This is a reference to the class this functions in appended to.
    :param object context: The context of the object this function is appended to.
    :return list: Result of get_rig_templates.
    """
    items = get_rig_templates()
    global _result_reference_get_rig_templates
    _result_reference_get_rig_templates = items
    return items
