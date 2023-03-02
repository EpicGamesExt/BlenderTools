# Copyright Epic Games, Inc. All Rights Reserved.

import os
import bpy
import json
import shutil
import tempfile
from ..constants import ToolInfo, Template
from ..dependencies import unreal


def get_settings():
    """
    Gets the settings from a file.

    :return dict: A dictionary of settings.
    """
    settings_path = os.path.join(
        os.path.dirname(__file__),
        os.pardir,
        'resources',
        'settings.json'
    )
    with open(settings_path) as settings_file:
        return json.load(settings_file)


def get_last_property_group_in_module_path(property_group, property_group_names):
    """
    Gets the last property group in the given module path.

    :param PropertyGroup property_group: A property group instance.
    :param list[str] property_group_names: A hierarchical list of property group name.
    :return PropertyGroup: A property group instance.
    """
    if len(property_group_names) > 0:
        sub_property_group_name = property_group_names.pop(0)
        sub_property_group = getattr(property_group, sub_property_group_name)
        return get_last_property_group_in_module_path(sub_property_group, property_group_names)
    else:
        return property_group


def get_property_by_path(settings_category, property_name, properties):
    """
    Gets a property using its dictionary path.

    :param str settings_category: The name of the settings category.
    :param str property_name: The name of the property.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return object: A property type instance.
    """
    property_group = get_last_property_group_in_module_path(properties, settings_category.split('.'))
    return getattr(property_group, property_name)


def get_settings_by_path(settings_category, settings_group):
    """
    Gets a dictionary of property attributes using its dictionary path.

    :param str settings_category: The name of the settings category.
    :param str settings_group: The name of the settings group.
    :return dict: A dictionary of property attributes.
    """
    settings = get_settings()
    for key in settings_category.split('-'):
        settings = settings[key]
    return settings[settings_group]


def merge_groups(property_group, settings_group, path=None, only_key=None):
    """
    Merges the property group and settings group values.
    """
    if path is None:
        path = []

    for key in settings_group:
        if not isinstance(key, str):
            raise RuntimeError(f'{key} is not a string!')

        if key in property_group:
            if isinstance(property_group[key], dict) and isinstance(settings_group[key], dict):
                merge_groups(property_group[key], settings_group[key], path + [str(key)], only_key)
        else:
            if only_key:
                if key == only_key:
                    property_group[key] = settings_group[key]
            else:
                property_group[key] = settings_group[key]

    return property_group


def get_generated_prefix(settings_category, settings_group):
    """
    Gets the prefixed path before the property.

    :param str settings_category: The name of the settings category.
    :param str settings_group: The name of the settings group.
    :return str: The generated property prefix.
    """
    return f'{settings_category.replace("-", ".")}.{settings_group}'


def get_setting_names(settings_category=None, settings_group=None):
    """
    Gets the names of the settings in the group

    :param str settings_category: The name of the settings category.
    :param str settings_group: The name of the settings group.
    :return list: A list of settings names.
    """
    settings = get_settings()
    if settings_category and settings_group:
        settings = get_settings_by_path(settings_category, settings_group)

    return [key for key, value in settings.items() if value.get('type')]


def get_template_folder():
    """
    Gets the file path to the temp folder.

    :return str: The file path to the temp folder.
    """
    return os.path.join(
        tempfile.gettempdir(),
        ToolInfo.APP.value,
        ToolInfo.NAME.value,
        Template.NAME
    )


def get_template_path(template_name):
    """
    Gets the full file path of the template file.

    :param str template_name: The name of the settings group.
    :return str: The full file path of the template file.
    """
    return os.path.join(
        get_template_folder(),
        template_name
    )


def get_template_version(file_path):
    """
    Gets the version of the given template file.

    :param str file_path: The full file path of the template file.
    :return int: The version number of the template.
    """
    with open(file_path, 'r') as template_file:
        data = json.load(template_file)
        return data.get('template_version')


def get_property_group_as_dictionary(property_group, extra_attributes=False):
    """
    Get values from a property group as a json serializable dictionary.

    :param PropertyGroup property_group: A property group instance.
    :param bool extra_attributes: Whether or not to include extra attributes.
    :return dict: A json serializable dictionary of the property group.
    """
    data = {}

    for key in [attribute for attribute in dir(property_group) if not attribute.startswith(('__', 'bl_', 'rna_'))]:

        property_type_name = None
        property_instance = property_group.__annotations__.get(key)
        value = getattr(property_group, key)

        # skip if this is a function
        if type(property_instance).__name__ in ['function', 'staticmethod']:
            continue

        if property_instance:
            property_type_name = property_instance.function.__name__

        # if the property is another property group, then call this again
        if hasattr(value, 'rna_type') and isinstance(value.rna_type, bpy.types.PropertyGroup):
            data[key] = get_property_group_as_dictionary(value, extra_attributes)

        elif property_type_name in ['IntVectorProperty', 'FloatVectorProperty']:
            data[key] = value[:]
            if extra_attributes:
                data[key] = {'value': value[:]}

        elif property_type_name:
            data[key] = value
            if extra_attributes:
                data[key] = {'value': value}

    return data


def get_extra_property_group_data_as_dictionary(property_group, only_key=None):
    """
    Gets the combination of the property group values and the extra data in the from the settings.

    :param PropertyGroup property_group: A property group instance.
    :param str only_key: The only key value that you want to be merges from the settings.
    """
    property_group_data = get_property_group_as_dictionary(property_group, extra_attributes=True)
    settings_group_data = get_settings()
    return merge_groups(property_group_data, settings_group_data, only_key=only_key)


def get_rpc_response_timeout(self):
    """
    Overrides getter method for the rpc_response_timeout property.
    """
    return self.get('rpc_response_timeout', 60)


def set_property_group_with_dictionary(property_group, data):
    """
    Sets the given property group to the values in the provided dictionary.

    :param PropertyGroup property_group: A property group instance.
    :param dict data: A json serializable dictionary of the property group.
    """
    for attribute in dir(property_group):
        property_type_name = None
        deferred_data = property_group.__annotations__.get(attribute)

        # skip if the attribute is a function
        if type(deferred_data).__name__ in ['function', 'staticmethod']:
            continue

        if deferred_data:
            property_type_name = deferred_data.function.__name__

        value = getattr(property_group, attribute)

        # if the property is another property group, then call this again
        if hasattr(value, 'rna_type') and isinstance(value.rna_type, bpy.types.PropertyGroup):
            set_property_group_with_dictionary(value, data.get(attribute, {}))

        elif property_type_name and data.get(attribute) is not None:
            setattr(property_group, attribute, data.get(attribute))


def set_rpc_response_timeout(self, value):
    """
    Overrides setter method on rpc_response_timeout property to update the
    environment variable on the rpc instance as well.
    """
    if unreal.is_connected():
        unreal.set_rpc_env('RPC_TIME_OUT', value)
    os.environ['RPC_TIME_OUT'] = str(value)
    self['rpc_response_timeout'] = value


def set_active_template(self=None, context=None):
    """
    Sets the active template.

    :param object self: This is a reference to the class this functions in appended to.
    :param object context: The context of the object this function is appended to.
    :return list: A list of tuples that define the settings template enumeration.
    """
    # this prevents path validations from triggering when the template values are set.
    bpy.context.window_manager.send2ue.path_validation = False
    with open(get_template_path(self.active_settings_template), 'r') as template_file:
        data = json.load(template_file)
        set_property_group_with_dictionary(
            self,
            data
        )
    bpy.context.window_manager.send2ue.path_validation = True


def create_property(data):
    """
    Creates a property instances from a dictionary.

    :param dict data: A dictionary that contains various properties.
    :return object: A property instance.
    """
    if type(data).__name__ == '_PropertyDeferred':
        return data

    if data.get('type') == 'STRING':
        return bpy.props.StringProperty(
            name=data.get('name'),
            description=data.get('description').strip('.'),
            default=data.get('default')
        )
    if data.get('type') == 'BOOLEAN':
        return bpy.props.BoolProperty(
            name=data.get('name'),
            description=data.get('description').strip('.'),
            default=data.get('default')
        )
    if data.get('type') == 'FLOAT':
        return bpy.props.FloatProperty(
            name=data.get('name'),
            description=data.get('description').strip('.'),
            default=data.get('default'),
            unit=data.get('unit', 'NONE'),
            subtype=data.get('subtype', 'NONE'),
            min=data.get('min', -3.402823e+38),
            max=data.get('max', 3.402823e+38)
        )
    if data.get('type') == 'INT':
        return bpy.props.IntProperty(
            name=data.get('name'),
            description=data.get('description').strip('.'),
            default=data.get('default'),
            subtype=data.get('subtype', 'NONE'),
            min=data.get('min', -2 ** 31),
            max=data.get('max', 2 ** 31 - 1)
        )
    if data.get('type') == 'FLOATVECTOR':
        return bpy.props.FloatVectorProperty(
            name=data.get('name'),
            description=data.get('description').strip('.'),
            default=data.get('default'),
            size=data.get('size', 3),
            unit=data.get('unit', 'NONE'),
            subtype=data.get('subtype', 'NONE'),
            min=data.get('min', -3.402823e+38),
            max=data.get('max', 3.402823e+38)
        )
    if data.get('type') == 'INTVECTOR':
        return bpy.props.IntVectorProperty(
            name=data.get('name'),
            description=data.get('description').strip('.'),
            default=data.get('default'),
            size=data.get('size', 3),
            subtype=data.get('subtype', 'NONE'),
            min=data.get('min', -2 ** 31),
            max=data.get('max', 2 ** 31 - 1)
        )
    if data.get('type') == 'ENUM':
        return bpy.props.EnumProperty(
            name=data.get('name'),
            description=data.get('description').strip('.'),
            items=[tuple(enum_item) for enum_item in data.get('enum_items', [])],
            default=data.get('default')
        )


def create_property_group(class_name, properties, methods):
    """
    Creates a property group instance given a name and the annotation data.

    :param str class_name: A snake case name.
    :param dict properties: A dictionary of property references.
    :param dict methods : A dictionary of methods on the property group.
    :return PointerProperty: A reference to the created property group.
    """
    property_group_class = create_property_group_class(class_name, properties, methods)
    bpy.utils.register_class(property_group_class)
    return bpy.props.PointerProperty(type=property_group_class)


def create_default_template():
    """
    Creates the default template in the template folder.
    """
    template_folder = get_template_folder()
    if not os.path.exists(template_folder):
        os.makedirs(template_folder)

    shutil.copy(
        os.path.join(ToolInfo.RESOURCE_FOLDER.value, 'setting_templates', Template.DEFAULT),
        os.path.join(template_folder, Template.DEFAULT)
    )


def create_property_group_class(class_name, properties, methods=None):
    """
    Creates a property group class given a name and the annotation data.

    :param str class_name: A snake case name.
    :param dict properties: A dictionary of property references.
    :param dict methods : A dictionary of methods on the property group.
    :return PropertyGroup: A reference to the created property group class.
    """
    if not methods:
        methods = {}

    attributes = {
        '__annotations__': properties,
        **methods
    }

    # make class name pascal case
    class_name = ''.join([
        word.capitalize() for word in f'{ToolInfo.NAME.value}_settings_group_{class_name}'.split('_')
    ])

    return type(
        class_name,
        (bpy.types.PropertyGroup,),
        attributes
    )


def save_template(template_file_path):
    """
    Saves the given template.

    :param str template_file_path: The full file path of the template file.
    """
    properties = getattr(bpy.context.scene, ToolInfo.NAME.value, None)
    if properties:
        file_path, extension = os.path.splitext(template_file_path)
        data = get_property_group_as_dictionary(properties)

        # remove ignored properties so they are not saved,
        for property_name in Template.IGNORED_PROPERTIES:
            data.pop(property_name, None)

        with open(f'{file_path}.json', 'w') as template_file:
            json.dump(data, template_file, indent=2)


def list_templates():
    """
    Lists the templates in the template folder.

    :return tuple: A tuple list of lists for values, labels, and tool tips.
    """
    template_values = []
    template_labels = []
    template_tool_tips = []

    template_folder = get_template_folder()

    if os.path.exists(template_folder):
        values = next(os.walk(template_folder))[2]
        for value in values:
            file_path = os.path.join(template_folder, value)
            if get_template_version(file_path) == Template.VERSION:
                template_values.append(value)
                template_labels.append(value.replace('_', ' ').capitalize().split('.')[0])
                template_tool_tips.append(file_path)

        # TODO notify the user that they have an old template version and that it needs to be converted
        # also provide a function that does the conversion for them
        # else:
        #     utilities.report_error()

    return template_values, template_labels, template_tool_tips


def populate_settings_template_dropdown(self=None, context=None):
    """
    This function populates enumeration for the settings template selection.

    :param object self: This is a reference to the class this functions in appended to.
    :param object context: The context of the object this function is appended to.
    :return list: A list of tuples that define the settings template enumeration.
    """
    data = []
    values, labels, tool_tips = list_templates()
    for index in range(len(values)):
        data.append(
            (values[index], labels[index], tool_tips[index], 'NONE', index)
        )
    return data


def load_template(load_path):
    """
    Loads the given template path into the template folder.

    :param str load_path: The full file path of the template file.
    """
    template_name = os.path.basename(load_path)
    template_location_path = get_template_path(template_name)
    shutil.copy(load_path, template_location_path)


def remove_template(properties):
    """
    Removes the active template from the addon's rig templates folder.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    # delete the selected rig template folder
    file_path = get_template_path(properties.active_settings_template)
    if os.path.exists(file_path) and properties.active_settings_template != Template.DEFAULT:
        os.remove(file_path)

    # set the selected rig template to the default
    properties.active_settings_template = Template.DEFAULT


def convert_to_property_group(data):
    """
    Converts a dictionary of json serializable types to bpy property types and groups.

    :param dict data: A dictionary of json serializable types.
    :return dict: A dictionary of property references.
    """
    for key, value in data.items():
        if type(value).__name__ == '_PropertyDeferred':
            data[key] = create_property(value)
            continue

        if type(value).__name__ in ['function', 'staticmethod']:
            continue

        if not value.get('name'):
            data[key] = create_property_group(
                class_name=key.upper(),
                properties=convert_to_property_group(data.get(key, {})),
                methods={key: value for key, value in value.items() if type(value).__name__ in ['function', 'staticmethod']}
            )
        else:
            data[key] = create_property(value)

    return data
