
import os
import sys


# set the python path to build_scripts directory and import the test_utils
sys.path.append(os.getcwd())
import blender_utilities  # noqa: E402


if __name__ == '__main__':
    # set the python path and current working to the test_cases directory
    test_cases_path = os.path.normpath(os.path.join(os.getcwd(), os.pardir, 'unit_tests'))
    sys.path.append(test_cases_path)

    # set this environment variable so that errors are thrown instead of being displayed to the user
    os.environ['DEV'] = '1'

    # get the normalized OS agnostic path to the .blend file that will be tested
    os.environ['BLENDS'] = os.path.normpath(
            os.path.join(
                os.getcwd(),
                os.pardir,
                'blends'
            )
    )

    blender_utilities.install_addons(['send2ue', 'ue2rigify'])
    blender_utilities.run_tests(test_cases_path)
