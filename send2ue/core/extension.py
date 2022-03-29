# Copyright Epic Games, Inc. All Rights Reserved.

import os
import bpy
import sys
import ast
import importlib.util
import tempfile
from . import settings
from abc import abstractmethod
from ..constants import ToolInfo, Extensions, ExtensionOperators
from . import utilities


class ExtensionBase:
    # Set this to a list of operator classes that will
    # be registered and added to the utilities submenu
    utility_operators = []

    @property
    @abstractmethod
    def name(self):
        """
        The name of the extension that all properties and operators will be namespaced under.
        """
        pass

    def draw_validations(self, dialog, layout):
        """
        Can be overridden to draw an interface for the extension under the validations tab.

        :param Send2UeSceneProperties self: The scene property group that contains all the addon properties.
        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        """
        pass

    def draw_export(self, dialog, layout):
        """
        Can be overridden to draw an interface for the extension under the export tab.

        :param Send2UeSceneProperties self: The scene property group that contains all the addon properties.
        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        """
        pass

    def draw_import(self, dialog, layout):
        """
        Can be overridden to draw an interface for the extension under the import tab.

        :param Send2UeSceneProperties self: The scene property group that contains all the addon properties.
        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        """
        pass

    def pre_operation(self):
        """
        Defines the pre operation logic that will be run before the send to unreal operation.

        :param Send2UeSceneProperties self: The scene property group that contains all the addon properties.
        """
        pass

    def pre_validations(self):
        """
        Defines the pre validation logic that will be an injected operation.

        :param Send2UeSceneProperties self: The scene property group that contains all the addon properties.
        """
        pass

    def post_validations(self):
        """
        Defines the post validation logic that will be an injected operation.

        :param Send2UeSceneProperties self: The scene property group that contains all the addon properties.
        """
        pass

    def pre_animation_export(self):
        """
        Defines the pre animation export logic that will be an injected operation.

        :param Send2UeSceneProperties self: The scene property group that contains all the addon properties.
        """
        pass

    def post_animation_export(self):
        """
        Defines the post animation export logic that will be an injected operation.

        :param Send2UeSceneProperties self: The scene property group that contains all the addon properties.
        """
        pass

    def pre_mesh_export(self):
        """
        Defines the pre mesh export logic that will be an injected operation.

        :param Send2UeSceneProperties self: The scene property group that contains all the addon properties.
        """
        pass

    def post_mesh_export(self):
        """
        Defines the post mesh export logic that will be an injected operation.

        :param Send2UeSceneProperties self: The scene property group that contains all the addon properties.
        """
        pass

    def pre_import(self):
        """
        Defines the pre import logic that will be an injected operation.

        :param Send2UeSceneProperties self: The scene property group that contains all the addon properties.
        """
        pass

    def post_import(self):
        """
        Defines the post import logic that will be an injected operation.

        :param Send2UeSceneProperties self: The scene property group that contains all the addon properties.
        """
        pass

    def post_operation(self):
        """
        Defines the post operation logic that will be run after the send to unreal operation.

        :param Send2UeSceneProperties self: The scene property group that contains all the addon properties.
        """
        pass


class ExtensionCollector(ast.NodeVisitor):
    """
    Collects Extensions.
    """

    def __init__(self, file_path):
        super(ExtensionCollector, self).__init__()
        self._extension_module = self.get_module(file_path)
        self._extension_classes = []

        with open(file_path) as extension_file:
            parsed_file = ast.parse(extension_file.read())
            self.visit(parsed_file)

    @staticmethod
    def get_module(file_path):
        """
        Gets the module from the file path.
        """
        path = os.path.dirname(file_path)
        name, file_extension = os.path.splitext(os.path.basename(file_path))
        if path not in sys.path:
            sys.path.insert(0, path)
        module = importlib.import_module(name)
        importlib.reload(module)

        # remove to prevent root module naming conflicts
        sys.path.remove(path)
        return module

    def get_extension_classes(self):
        """
        Gets the Extension classes.

        :return ExtensionBase: A test suite.
        """
        return self._extension_classes

    def visit_ClassDef(self, node):
        """
        Override the method that visits nodes that are classes.
        """
        extension_class = getattr(self._extension_module, node.name)

        if issubclass(extension_class, ExtensionBase):
            self._extension_classes.append(extension_class)


class ExtensionFactory:
    def __init__(self):
        self.temp_path = os.path.join(
            tempfile.gettempdir(),
            ToolInfo.APP.value,
            ToolInfo.NAME.value,
            Extensions.NAME
        )
        self.source_path = Extensions.FOLDER

    @staticmethod
    def _get_utility_operators(extension_class):
        """
        Gets the utility operators that will be added to the utilities menu. This overrides the bl_idname
        so that the operators are namespaced correctly.

        :param ExtensionBase extension_class: An implement extension class.
        :return list: A list of operators.
        """
        utility_operators = []
        for operator_class in extension_class.utility_operators:
            bl_idname = (
                f'{ToolInfo.NAME.value}.{Extensions.NAME}_{extension_class.name}_'
                f'{Extensions.UTILITY_OPERATOR}_{operator_class.__name__.lower()}'
            )
            operator_class.bl_idname = bl_idname[:61] if len(bl_idname) > 61 else bl_idname
            utility_operators.append(operator_class)
        return utility_operators

    def _get_extension_classes(self):
        """
        Gets the extension classes.
        """
        extensions = []

        # add in the additional extensions from the addons preferences
        addon = bpy.context.preferences.addons.get(ToolInfo.NAME.value)
        if addon and addon.preferences:
            if os.path.exists(addon.preferences.extensions_repo_path):
                for file_name in os.listdir(addon.preferences.extensions_repo_path):
                    name, file_extension = os.path.splitext(file_name)
                    if file_extension == '.py':
                        extension_collector = ExtensionCollector(
                            os.path.join(addon.preferences.extensions_repo_path, file_name)
                        )
                        extensions.extend(extension_collector.get_extension_classes())

        # add in the extensions that shipped with the addon
        for file_name in os.listdir(self.source_path):
            name, file_extension = os.path.splitext(file_name)
            if file_extension == '.py':
                extension_collector = ExtensionCollector(os.path.join(self.source_path, file_name))
                extensions.extend(extension_collector.get_extension_classes())
        return extensions

    def create_operators(self):
        """
        Gets the extension operators.
        """
        operator_classes = []

        for extension_class in self._get_extension_classes():
            for attribute, value in extension_class.__dict__.items():
                if type(value).__name__ == 'function':
                    bl_idname = (
                        f'{ToolInfo.NAME.value}.{Extensions.NAME}_{extension_class.name}_{value.__name__}'
                    )
                    if value.__name__ in [item.value for item in ExtensionOperators]:
                        # dynamically create operator classes to hold the functions in their execute method
                        operator_classes.append(utilities.create_operator(bl_idname, value))

            # get the utility operators on the class as well
            operator_classes.extend(self._get_utility_operators(extension_class))

        # register the extension operators
        for operator_class in operator_classes:
            if not utilities.get_operator_class_by_bl_idname(operator_class.bl_idname):
                bpy.utils.register_class(operator_class)

    def get_properties(self):
        """
        Gets the property data of the extension.
        """
        data = settings.get_settings()
        data[Extensions.NAME] = {}

        for extension_class in self._get_extension_classes():
            data[Extensions.NAME][extension_class.name] = {}

            if hasattr(extension_class, '__annotations__'):
                for attribute, value in extension_class.__annotations__.items():
                    data[Extensions.NAME][extension_class.name][attribute] = value

        return settings.create_property_group_class(
            class_name=f"{ToolInfo.NAME.value}SettingsGroup",
            data=settings.convert_to_properties(data)
        )

    def create_draws(self):
        """
        Sets the extensions draw methods.
        """
        for extension_class in self._get_extension_classes():
            for draw_tab in Extensions.DRAW_TABS:
                draw_function = extension_class.__dict__.get(draw_tab)
                if draw_function:
                    namespace = f'{ToolInfo.NAME.value}_{Extensions.NAME}_{extension_class.name}_{draw_tab}'
                    bpy.app.driver_namespace[namespace] = draw_function

    @staticmethod
    def remove_property_data():
        """
        Removes all extension property data from the scene.
        """
        # delete the scene data block for the extensions if they exist
        if bpy.context.scene.get(ToolInfo.NAME.value, {}).get(Extensions.NAME):
            del bpy.context.scene[ToolInfo.NAME.value][Extensions.NAME]

    @staticmethod
    def remove_operators():
        """
        Removes all extension operators.
        """
        for class_name in dir(bpy.types):
            if class_name.startswith(f'{ToolInfo.NAME.value.upper()}_OT_{Extensions.NAME}_'):
                operator_class = getattr(bpy.types, class_name)
                bpy.utils.unregister_class(operator_class)

    @staticmethod
    def remove_draws():
        """
        Removes all draw methods.
        """
        # get the draw extension keys
        keys = [
            key for key in bpy.app.driver_namespace.keys()
            if key.startswith(f'{ToolInfo.NAME.value}_{Extensions.NAME}_')
        ]

        # remove the draw extension keys
        for key in keys:
            bpy.app.driver_namespace.pop(key)


def run_operators(name_space):
    """
    Runs the operators in the given name space.

    :param str name_space: The name space of the operators to run.
    """
    operator_namespace = getattr(bpy.ops, ToolInfo.NAME.value, None)
    if operator_namespace:
        for attribute in dir(operator_namespace):
            if attribute.startswith(f'{Extensions.NAME}_') and attribute.endswith(f'_{name_space}'):
                operator = getattr(operator_namespace, attribute)
                operator()
