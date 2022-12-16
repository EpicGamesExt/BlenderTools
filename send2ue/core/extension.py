# Copyright Epic Games, Inc. All Rights Reserved.

import os
import bpy
import sys
import ast
import importlib.util
import tempfile
from . import settings
from abc import abstractmethod
from ..constants import ToolInfo, Extensions, ExtensionTasks
from . import utilities


def run_extension_filters(armature_objects, mesh_objects, hair_objects):
    """
    Runs all the filter methods on the registered extensions. The result with be the intersection of
    all filter methods.

    :param list[bpy.types.Object] armature_objects: The name space of the task to run.
    :param list[bpy.types.Object] mesh_objects: The name space of the task to run.
    :param list[Any] hair_objects: The name space of the task to run.
    :returns: A tuple which is a filtered list of armature objects, and a filtered list of meshes objects.
    :rtype: tuple(list, list)
    """
    for attribute in dir(bpy.context.scene.send2ue.extensions):
        filter_objects = getattr(
            getattr(bpy.context.scene.send2ue.extensions, attribute, object),
            ExtensionTasks.FILTER_OBJECTS.value,
            None
        )
        if filter_objects:
            filtered_armature_objects, filtered_mesh_objects, filtered_hair_objects = filter_objects(
                armature_objects,
                mesh_objects,
                hair_objects,
            )

            # get the intersection of the previous list values and the new filtered
            armature_objects = set(armature_objects).intersection(filtered_armature_objects)
            mesh_objects = set(mesh_objects).intersection(filtered_mesh_objects)
            hair_objects = set(hair_objects).intersection(filtered_hair_objects)

            # reorder the objects by name
            armature_objects = sorted(armature_objects, key=lambda obj: obj.name)
            mesh_objects = sorted(mesh_objects, key=lambda obj: obj.name)
            hair_objects = sorted(hair_objects, key=lambda obj: obj.name)

    return list(armature_objects), list(mesh_objects), list(hair_objects)


def run_extension_tasks(name_space):
    """
    Runs the task in the given name space.

    :param str name_space: The name space of the task to run.
    """
    for attribute in dir(bpy.context.scene.send2ue.extensions):
        task = getattr(getattr(bpy.context.scene.send2ue.extensions, attribute, object), name_space, None)
        if task:
            args = []
            asset_id = bpy.context.window_manager.send2ue.asset_id
            asset_data = bpy.context.window_manager.send2ue.asset_data.get(asset_id)

            # if there is current asset data add it to the args
            if name_space not in [ExtensionTasks.PRE_OPERATION.value, ExtensionTasks.POST_OPERATION.value]:
                args.append(asset_data)

            # add the addon properties to the args
            args.append(bpy.context.scene.send2ue)

            # call the task
            task(*args)


class ExtensionBase:
    # Set this to a list of operator classes that will be registered and added to the utilities submenu.
    utility_operators = []

    @property
    @abstractmethod
    def name(self):
        """
        The name of the extension that all properties and operators will be namespaced under.
        """
        raise NotImplementedError('A name must be defined for the extension class.')

    def draw_validations(self, dialog, layout, properties):
        """
        Can be overridden to draw an interface for the extension under the validations tab.

        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        pass

    def draw_export(self, dialog, layout, properties):
        """
        Can be overridden to draw an interface for the extension under the export tab.

        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        pass

    def draw_import(self, dialog, layout, properties):
        """
        Can be overridden to draw an interface for the extension under the import tab.

        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        pass

    def draw_paths(self, dialog, layout, properties):
        """
        Can be overridden to draw an interface for the extension under the paths tab.

        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        pass

    def pre_operation(self, properties):
        """
        Defines the pre operation logic that will be run before the send to unreal operation.

        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        pass

    def pre_validations(self, properties):
        """
        Defines the pre validation logic that will be an injected operation.

        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        :returns: Whether or not the validation has passed.
        :rtype: bool
        """
        pass

    def post_validations(self,  properties):
        """
        Defines the post validation logic that will be an injected operation.

        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        :returns: Whether or not the validation has passed.
        :rtype: bool
        """
        pass

    def pre_animation_export(self, asset_data, properties):
        """
        Defines the pre animation export logic that will be an injected operation.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        pass

    def post_animation_export(self, asset_data, properties):
        """
        Defines the post animation export logic that will be an injected operation.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        pass

    def pre_mesh_export(self, asset_data, properties):
        """
        Defines the pre mesh export logic that will be an injected operation.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        pass

    def post_mesh_export(self, asset_data, properties):
        """
        Defines the post mesh export logic that will be an injected operation.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        pass

    def pre_groom_export(self, asset_data, properties):
        """
        Defines the pre groom export logic that will be an injected operation.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        pass

    def post_groom_export(self, asset_data, properties):
        """
        Defines the post groom export logic that will be an injected operation.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        pass

    def pre_import(self, asset_data, properties):
        """
        Defines the pre import logic that will be an injected operation.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        pass

    def post_import(self, asset_data, properties):
        """
        Defines the post import logic that will be an injected operation.

        :param dict asset_data: A mutable dictionary of asset data for the current asset.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        pass

    def post_operation(self, properties):
        """
        Defines the post operation logic that will be run after the send to unreal operation.

        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        pass

    def filter_objects(self, armature_objects, mesh_objects, hair_objects):
        """
        Defines a filter for the armature and mesh objects after they have been initially collected.

        :param list[object] armature_objects: A list of armature objects.
        :param list[object] mesh_objects: A list of mesh objects.
        :param list[object] hair_objects: A list of hair objects.
        :returns: A tuple which is a filtered list of armature objects, and a filtered list of meshes objects.
        :rtype: tuple(list, list, list)
        """
        return armature_objects, mesh_objects, hair_objects

    def update_asset_data(self, asset_data):
        """
        Updates the asset data dictionary on the current asset.

        :param dict asset_data: The asset data dictionary.
        """
        asset_id = bpy.context.window_manager.send2ue.asset_id
        bpy.context.window_manager.send2ue.asset_data[asset_id].update(asset_data)


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

        :return list: A list of extensions.
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
                f'{ToolInfo.NAME.value}.{Extensions.NAME}_{extension_class.name}_{operator_class.__name__.lower()}'
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

    def create_utility_operators(self):
        """
        Creates all the extensions utility operators.
        """
        operator_classes = []

        for extension_class in self._get_extension_classes():
            # get the utility operators on the class
            operator_classes.extend(self._get_utility_operators(extension_class))

        # register the extension utility operators
        for operator_class in operator_classes:
            if not utilities.get_operator_class_by_bl_idname(operator_class.bl_idname):
                bpy.utils.register_class(operator_class)

    def get_property_group_class(self):
        """
        Gets the property data class of the extension.
        """
        data = settings.get_settings()
        data[Extensions.NAME] = {}

        for extension_class in self._get_extension_classes():
            data[Extensions.NAME][extension_class.name] = {}

            # get the properties
            if hasattr(extension_class, '__annotations__'):
                for attribute, value in extension_class.__annotations__.items():
                    data[Extensions.NAME][extension_class.name][attribute] = value

            # get the extension methods and its parent class methods
            for attribute, value in extension_class.__dict__.items():
                if type(value).__name__ in ['function', 'staticmethod']:
                    data[Extensions.NAME][extension_class.name][attribute] = value

            # add the update asset method to the class
            data[Extensions.NAME][extension_class.name]['update_asset_data'] = ExtensionBase.update_asset_data

        return settings.create_property_group_class(
            class_name=f"{ToolInfo.NAME.value}SettingsGroup",
            properties=settings.convert_to_property_group(data=data)
        )

    @staticmethod
    def remove_property_data():
        """
        Removes all extension property data from the scene.
        """
        # delete the scene data block for the extensions if they exist
        if bpy.context.scene.get(ToolInfo.NAME.value, {}).get(Extensions.NAME):
            del bpy.context.scene[ToolInfo.NAME.value][Extensions.NAME]

    @staticmethod
    def remove_utility_operators():
        """
        Removes all extension utility operators.
        """
        for class_name in dir(bpy.types):
            if class_name.startswith(f'{ToolInfo.NAME.value.upper()}_OT_{Extensions.NAME}_'):
                operator_class = getattr(bpy.types, class_name)
                bpy.utils.unregister_class(operator_class)
