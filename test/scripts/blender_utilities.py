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


def get_addon_folder_path(addon_name):
    """
    This function builds the full path to the provided addon folder.

    :param str addon_name: The name of the addon that you would like to get the full path to.
    :return str: The full path of the addon.
    """
    # get the path to the addon folder
    return os.path.normpath(os.path.join(
        os.getcwd(),
        os.pardir,
        os.pardir,
        addon_name,
        'addon'
    ))


def get_log_file_path():
    """
    This function get the full path to the log file and create the log folder if needed.
    """
    log_file_path = os.path.normpath(os.path.join(
        os.getcwd(),
        os.pardir,
        'logs', 'unittest_results.log')
    )

    if not os.path.exists(os.path.dirname(log_file_path)):
        os.makedirs(os.path.dirname(log_file_path))

    return log_file_path


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
        send_to_unreal_addon_path = get_addon_folder_path(module_name)

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

    if sys.argv[-1].lower() == '--ci':
        blender_path = os.environ.get('BLENDER_EXE', '/home/ue4/blender/blender')
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

    # use environment variable to override test cases
    test_cases = os.environ.get('TEST_CASES')
    if test_cases:
        unit_test_modules = [test_case_file.replace('.py', '') for test_case_file in test_cases.split(',')]

    suite = unittest.TestSuite()

    for unit_test_module in unit_test_modules:
        module = importlib.import_module(unit_test_module)
        for class_name in dir(module):
            if not class_name.islower():
                test_class = getattr(module, class_name)
                suite.addTest(unittest.makeSuite(test_class))

    # pass a log file with write permissions into the test runner
    log_file_path = get_log_file_path()
    write_log_file = open(log_file_path, 'w')
    tests = unittest.TextTestRunner(write_log_file, verbosity=2)

    # run the unittests
    result = tests.run(suite)
    write_log_file.close()

    # if a test case fails, let the parent python process know there was a failure
    failure_count = len(result.failures + result.errors)
    if failure_count != 0:
        sys.exit(1)
