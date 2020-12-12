#  Copyright Epic Games, Inc. All Rights Reserved.

import os
import shutil
import logging
import ast
import sys

try:
    import bpy
    import addon_utils
except ModuleNotFoundError:
    pass


class AddonManager:

    def __init__(self, addon_name):
        """
        Initializes the class and sets the addon module name.
        """
        self.addon_name = addon_name

    def get_dict_from_python_file(self, python_file, dict_name):
        """
        This method gets the first dictionary from the given file that matches the given variable name.

        :param object python_file: A file object to read from.
        :param str dict_name: The variable name of a dictionary.
        :return dict: The value of the dictionary.
        """
        dictionary = {}
        tree = ast.parse(python_file.read())

        for item in tree.body:
            if hasattr(item, 'targets'):
                for target in item.targets:
                    if target.id == dict_name:
                        for index, key in enumerate(item.value.keys):
                            # add string as dictionary value
                            if hasattr(item.value.values[index], 's'):
                                dictionary[key.s] = item.value.values[index].s

                            # add number as dictionary value
                            elif hasattr(item.value.values[index], 'n'):
                                dictionary[key.s] = item.value.values[index].n

                            # add list as dictionary value
                            elif hasattr(item.value.values[index], 'elts'):
                                list_value = []
                                for element in item.value.values[index].elts:
                                    # add a number to the list
                                    if hasattr(element, 'n'):
                                        list_value.append(element.n)

                                    # add a string to the list
                                    elif hasattr(element, 's'):
                                        list_value.append(element.s)

                                dictionary[key.s] = list_value
                        break
        return dictionary

    def get_addon_version_number(self, addon_folder_path):
        """
        This method gets the version number from the addons bl_info

        :param str addon_folder_path: The path to the addon folder.
        :return str: The version of the addon.
        """
        addon_init = open(os.path.join(addon_folder_path, '__init__.py'))

        bl_info = self.get_dict_from_python_file(addon_init, 'bl_info')
        version_numbers = [str(number) for number in bl_info['version']]
        version_number = '.'.join(version_numbers)
        return version_number

    def get_addon_zip_path(self, addon_folder_path):
        """
        This method gets the path to the addons zip file.

        :param str addon_folder_path: The path to the addon folder.
        :return str: The full path to the released zip file.
        """
        # get the versioned addon paths
        version_number = self.get_addon_version_number(addon_folder_path)
        addon_zip_file = f'{self.addon_name}_{version_number}.zip'
        release_folder_path = os.path.normpath(os.path.join(addon_folder_path, os.pardir, 'releases', addon_zip_file))

        return release_folder_path

    def set_folder_contents_permissions(self, folder_path, permission_level):
        """
        This method goes through all files and folders contained in the folder and modifies their permissions to
        the given permissions.

        :param str folder_path: The full path to the folder you would like to modify permissions on.
        :param octal permission_level: The octal permissions value.
        """
        for root, directories, files in os.walk(folder_path):
            for directory in directories:
                os.chmod(os.path.join(root, directory), permission_level)
            for file in files:
                os.chmod(os.path.join(root, file), permission_level)

    def addon_is_installed(self, addon_module_name):
        """
        This method checks if the given addon module is currently installed.

        :param str addon_module_name: The addon module name.
        :return bool: True or False depending on whether the addon exists.
        """
        addon_names = [module.bl_info.get('name') for module in addon_utils.modules()]

        for addon_name in addon_names:
            if addon_name == addon_module_name:
                return True
            else:
                return False

    def zip_addon_folder(self, addon_folder_path):
        """
        This method zips up the given addon.

        :param str addon_folder_path: The path to the addon folder.
        :return str: The full path to the zip file.
        """
        # get the folder paths
        versioned_zip_file_path = self.get_addon_zip_path(addon_folder_path)
        versioned_folder_path = versioned_zip_file_path.replace('.zip', '')

        # change the permissions to allow the folders contents to be modified.
        if sys.platform == 'win32':
            self.set_folder_contents_permissions(os.path.join(addon_folder_path, os.pardir), 0o777)

        # remove the existing zip archive
        if os.path.exists(versioned_zip_file_path):
            try:
                os.remove(versioned_zip_file_path)
            except PermissionError:
                logging.warning(f'Could not delete {versioned_folder_path}!')

        # copy the addon module in to the versioned directory with its addon module name as a sub directory
        shutil.copytree(addon_folder_path, os.path.join(versioned_folder_path, self.addon_name))

        # make a zip archive of the copied folder
        shutil.make_archive(versioned_folder_path, "zip", versioned_folder_path)

        # remove the copied directory
        shutil.rmtree(versioned_folder_path)

        # return the full path to the zip file
        return versioned_zip_file_path

    def build_addon(self, addon_folder_path):
        """
        This method builds the addon. If there are any custom steps in the build process that need to
        happen before the addon gets zipped, override this method in a subclass.

        :param str addon_folder_path: The path to the addon folder.
        :return str: The full path to the zip file.
        """
        return self.zip_addon_folder(addon_folder_path)

    def install_addon(self, addon_folder_path):
        """
        This method installs the addon to blender.

        :param str addon_folder_path: The path to the addon folder.
        """

        # install addon if it isn't installed
        if not self.addon_is_installed(self.addon_name):
            bpy.ops.preferences.addon_install(filepath=self.get_addon_zip_path(addon_folder_path))

        # enable addon if it is disabled
        if self.addon_name not in bpy.context.preferences.addons.keys():
            bpy.ops.preferences.addon_enable(module=self.addon_name)

    def uninstall_addon(self):
        """
        This method uninstalls the addon from blender.

        :param str addon_folder_path: The path to the addon folder.
        """
        # disable addon if it is enabled
        if self.addon_name in bpy.context.preferences.addons.keys():
            bpy.ops.preferences.addon_disable(module=self.addon_name)

        # remove addon if it is all ready installed
        if self.addon_is_installed(self.addon_name):
            bpy.ops.preferences.addon_remove(module=self.addon_name)
