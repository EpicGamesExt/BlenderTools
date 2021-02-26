# Copyright Epic Games, Inc. All Rights Reserved.

import unreal_utilities
import blender_utilities
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


if __name__ == '__main__':
    unreal_process = None

    try:
        # launch only blender and run the unit tests
        if os.environ.get('ONLY_BLENDER'):
            blender_utilities.launch_blender()

        # launch both blender and unreal run the unit tests
        else:
            # launch the unreal commandline process
            unreal_process = unreal_utilities.launch_unreal()

            # check for a running unreal editor before launching blender
            if unreal_utilities.is_unreal_running(attempts=60, ping=5):

                # launch blender and run the unit tests
                blender_utilities.launch_blender()
    finally:
        if unreal_process:
            unreal_utilities.close_unreal(unreal_process)

        # log the test results from the file
        log_file_path = blender_utilities.get_log_file_path()
        read_log_file = open(log_file_path, 'r')
        logger.info(f'\n{read_log_file.read()}')
        read_log_file.close()
