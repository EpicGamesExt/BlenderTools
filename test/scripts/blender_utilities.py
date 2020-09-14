# Copyright Epic Games, Inc. All Rights Reserved.

import os
import re
import sys
import logging
import unittest
import importlib
from addon_manager import AddonManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_blender_version_from_chocolatey(log_file_path):
    """
    This function searches the chocolately logs to get the recently installed blender version.

    :param str log_file_path: The full path to the chocolately log file.
    :return str: The version of the blender installation.
    """
    log_file = open(log_file_path)
    for line in log_file:
        if re.search(r'(blender v\d\.\d\d\.\d \[Approved\])', line):
            return line.replace('blender v', '').replace(' [Approved]', '')[:-3]

    raise RuntimeError('Could not determine the blender version from chocolatey logs!')


def get_addon_folder_path(addon_name):
    """
    This function builds the full path to the provided addon folder.

    :param str addon_name: The name of the addon that you would like to get the full path to.
    :return str: The full path of the addon.
    """
    # get the path to the addon folder
    return os.path.join(
        os.getcwd(),
        os.pardir,
        os.pardir,
        addon_name,
        'addon'
    )


def install_addons(addons):
    """
    This function installs a dictionary of addons.

    :param dict addons: This is a dictionary of key value pairs, where the key is the addon folder name
    in the git repository and the value is the module name of the addon.
    :return:
    """
    logger.info('Installing Blender addons...')
    for module_name in addons:

        # get the addon path
        send_to_unreal_addon_path = os.path.normpath(get_addon_folder_path(module_name))

        # build the addon
        addon = AddonManager(module_name)
        addon.build_addon(send_to_unreal_addon_path)

        # uninstall the addon if it exists
        addon.uninstall_addon()

        # install the addon
        addon.install_addon(send_to_unreal_addon_path)


def launch_blender():
    """
    This function runs through a list of unit test files on linux, mac, and windows.

    :param list test_files: A list of file names to run.
    """
    # define the flags passed to the blender application
    flags = '--background --disable-autoexec --python-exit-code 1 --python ./../unit_tests/main.py'

    if os.environ.get('CI'):

        # launch blender according to each operating system
        if sys.platform == 'linux':
            blender_path = '/home/ue4/blender/blender'

        # TODO macOS needs testing
        if sys.platform == 'darwin':
            blender_path = '/usr/local/bin/blender'

        if sys.platform == 'win32':
            # get the installed blender version using the chocolatey logs
            blender_version = get_blender_version_from_chocolatey(os.path.join(
                os.environ['PROGRAMDATA'],
                'chocolatey',
                'logs',
                'chocolatey.log'
            ))

            # build the full path to the blender executable
            blender_path = r'C:\Program Files\Blender Foundation\Blender {blender_version}\blender.exe'.format(
                blender_version=blender_version
            )

        blender_path = os.environ.get('BLENDER_EXE', blender_path)
    else:
        blender_path = os.environ.get('BLENDER_EXE', 'blender')

    command = f'"{blender_path}" {flags}'

    # run blender with the test case file and check for system errors
    logging.info('Launching Blender...')
    if os.system(command) != 0:
        sys.exit(1)


def run_tests(test_cases_folder):
    """
    This function builds a test suite from all the unit test files and runs the unit tests.
    """
    logging.info('Running unit tests...')
    # import all the unit tests
    _, _, unit_test_files = next(os.walk(test_cases_folder))
    unit_test_files.remove('main.py')
    unit_test_modules = [test_case_file.replace('.py', '') for test_case_file in unit_test_files]

    suite = unittest.TestSuite()

    for unit_test_module in unit_test_modules:
        module = importlib.import_module(unit_test_module)
        for class_name in dir(module):
            if not class_name.islower():
                test_class = getattr(module, class_name)
                suite.addTest(unittest.makeSuite(test_class))

    # pass a log file with write permissions into the test runner
    log_file_path = os.path.join(os.pardir, 'unittest_results.log')
    write_log_file = open(log_file_path, 'w')
    tests = unittest.TextTestRunner(write_log_file, verbosity=2)

    # run the unittests
    result = tests.run(suite)
    write_log_file.close()

    # log the test results from the file
    read_log_file = open(log_file_path, 'r')
    logger.info(read_log_file.read())
    read_log_file.close()

    # if a test case fails, let the parent python process know there was a failure
    failure_count = len(result.failures + result.errors)
    if failure_count != 0:
        sys.exit(1)