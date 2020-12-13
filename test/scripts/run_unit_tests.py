# Copyright Epic Games, Inc. All Rights Reserved.

import unreal_utilities
import blender_utilities
import logging
import subprocess
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def git_file_has_modifications(file):
    """
    Check git to see if file is modified.
    """
    proc = subprocess.run(
            ['git', 'ls-files', '--modified', file],
            cwd='../..',
            capture_output=True)

    if proc.returncode != 0:
        raise RuntimeError(f'git ls-files non-zero return code {proc.returncode}')

    dirty_files = [f for f in proc.stdout.decode('utf-8').splitlines()]

    return metarig_file in dirty_files


def git_checkout_file(file):
    """
    Run "git checkout file" to revert changes made to file.
    """

    proc = subprocess.run(['git', 'checkout', file], cwd='../..')
    if proc.returncode != 0:
        raise RuntimeError(f'git failed to checkout {file}. Return code is {proc.returncode}')


if __name__ == '__main__':

    # Make sure metarig.py has no modifications, since unit tests will modify it.
    metarig_file = 'ue2rigify/addon/resources/rig_templates/unreal_mannequin/metarig.py'
    if git_file_has_modifications(metarig_file):
        print(f'{metarig_file} has modifications that the unit tests will overwrite.\n'
              'Commit or revert your changes and then run the unit tests again.')
        sys.exit(1)

    # launch the unreal commandline process
    unreal_process = unreal_utilities.launch_unreal()

    try:
        # check for a running unreal editor before launching blender
        if unreal_utilities.is_unreal_running(attempts=60, ping=5):

            # launch blender and run the unit tests
            blender_utilities.launch_blender()
    finally:
        unreal_utilities.close_unreal(unreal_process)

        # log the test results from the file
        log_file_path = blender_utilities.get_log_file_path()
        read_log_file = open(log_file_path, 'r')
        logger.info(f'\n{read_log_file.read()}')
        read_log_file.close()

    git_checkout_file(metarig_file)
