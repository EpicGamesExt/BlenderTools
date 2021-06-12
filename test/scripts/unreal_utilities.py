# Copyright Epic Games, Inc. All Rights Reserved.

import os
import sys
import time
import signal
import logging
import threading
import subprocess

# import the remote execution module from the send to unreal addon
send_to_unreal_modules = os.path.normpath(
    os.path.join(
        os.getcwd(),
        os.pardir,
        os.pardir,
        'send2ue',
        'addon',
        'dependencies'
    )
)

sys.path.append(send_to_unreal_modules)
from remote_execution import RemoteExecution  # noqa: E402

unreal_response = ''

logger = logging.getLogger('remote_execution')
logger.setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

UNREAL = os.environ.get('UNREAL', 'UE4Editor-Cmd')


def run_unreal_python_commands(remote_exec, commands, attempts=50, ping=0.1):
    """
    This function finds the open unreal editor with remote connection enabled, and sends it python commands.

    :param object remote_exec: A RemoteExecution instance.
    :param str commands: A formatted string of python commands that will be run by the engine.
    :param int attempts : The number of times to try to make a connection.
    :param float ping: The amount of time in seconds in between attempts.
    """
    try:
        for attempt in range(1, attempts + 1):
            # wait the number of seconds defined by the ping before attempting to connect
            time.sleep(ping)
            # try to connect to an editor
            for node in remote_exec.remote_nodes:
                remote_exec.open_command_connection(node.get("node_id"))

            # if a connection is made
            if remote_exec.has_command_connection():
                # run the import commands and save the response in the global unreal_response variable
                global unreal_response
                unreal_response = remote_exec.run_command(commands, unattended=False)
                break

            # otherwise make an other attempt to connect to the engine
            else:
                logger.debug(f'Pinging the Unreal Editor {attempt*"."}')
                if attempt >= attempts:
                    remote_exec.stop()
                    raise RuntimeError("Could not find an open Unreal Editor instance!")

    # shutdown the connection
    finally:
        remote_exec.stop()


def get_lod_count(game_path, attempts=0):
    """
    This function gets the number of lods on the given asset.

    :param str game_path: The game path to the unreal asset.
    :param str attempts: The number of attempts to get the correct response.
    :return int: The number of lods on the asset.
    """
    # start a connection to the engine that lets you send python strings
    remote_exec = RemoteExecution()
    remote_exec.start()

    # TODO: EditorSkeletalMeshLibrary: Function 'get_lod_count' on 'EditorSkeletalMeshLibrary' is deprecated
    # TODO: EditorStaticMeshLibrary: Function 'get_lod_count' on 'EditorStaticMeshLibrary' is deprecated
    # send over the python code as a string
    run_unreal_python_commands(
        remote_exec,
        '\n'.join([
            f'lod_count=0',
            f'game_asset = unreal.load_asset(r"{game_path}")',
            f'if game_asset and game_asset.__class__.__name__ == "SkeletalMesh":',
            f'\tlod_count = unreal.EditorSkeletalMeshLibrary.get_lod_count(game_asset)',

            f'if game_asset and game_asset.__class__.__name__ == "StaticMesh":',
            f'\tlod_count = unreal.EditorStaticMeshLibrary.get_lod_count(game_asset)',
            f'if game_asset:',
            f'\tprint(lod_count)'
        ]))

    if unreal_response:
        if unreal_response['success']:
            output = unreal_response['output']
            if output:
                for line in output:
                    try:
                        return int(line['output'])
                    except ValueError as error:
                        logger.warning(error)

            if attempts < 10:
                return get_lod_count(game_path, attempts=attempts+1)


def asset_exists(game_path):
    """
    This function checks to see if an asset exist in unreal.

    :param str game_path: The game path to the unreal asset.
    :return bool: Whether or not the asset exists.
    """
    # start a connection to the engine that lets you send python strings
    remote_exec = RemoteExecution()
    remote_exec.start()

    # send over the python code as a string
    run_unreal_python_commands(
        remote_exec,
        '\n'.join([
            f'game_asset = unreal.load_asset(r"{game_path}")',
            f'if game_asset:',
            f'\tpass',
            f'else:',
            f'\traise RuntimeError("Asset not found")',
        ]))

    if unreal_response:
        return bool(unreal_response['success'])


def has_custom_collision(game_path):
    """
    This function checks to see if an asset has a custom collision.

    :param str game_path: The game path to the unreal asset.
    :return bool: Whether or not the asset has a custom collision or not.
    """
    # start a connection to the engine that lets you send python strings
    remote_exec = RemoteExecution()
    remote_exec.start()

    # send over the python code as a string
    run_unreal_python_commands(
        remote_exec,
        '\n'.join([
            f'game_asset = unreal.load_asset(r"{game_path}")',
            f'if game_asset:',
            f'\tif game_asset.get_editor_property("customized_collision"):',
            f'\t\tpass',
            f'else:',
            f'\traise RuntimeError("Asset has no collision")',
        ]))

    if unreal_response:
        return bool(unreal_response['success'])


def has_socket(game_path, socket_name):
    """
    This function checks to see if an asset has a socket.

    :param str game_path: The game path to the unreal asset.
    :param str socket_name: The name of the socket to look for.
    :return bool: Whether or not the asset has the given socket or not.
    """
    # start a connection to the engine that lets you send python strings
    remote_exec = RemoteExecution()
    remote_exec.start()

    # send over the python code as a string
    run_unreal_python_commands(
        remote_exec,
        '\n'.join([
            f'game_asset = unreal.load_asset(r"{game_path}")',
            f'if game_asset:',
            f'\tif not game_asset.find_socket("{socket_name}"):',
            f'\t\traise RuntimeError("Asset has no socket {socket_name}")',
        ]))

    if unreal_response:
        return bool(unreal_response['success'])


def delete_asset(game_path):
    """
    This function deletes an asset in unreal.

    :param str game_path: The game path to the unreal asset.
    """
    # start a connection to the engine that lets you send python strings
    remote_exec = RemoteExecution()
    remote_exec.start()

    # send over the python code as a string
    run_unreal_python_commands(
        remote_exec,
        '\n'.join([
            f'unreal.EditorAssetLibrary.delete_asset(r"{game_path}")',
        ]))


def delete_directory(directory_path):
    """
    This function deletes an folder and its contents in unreal.

    :param str directory_path: The game path to the unreal project folder.
    """
    # start a connection to the engine that lets you send python strings
    remote_exec = RemoteExecution()
    remote_exec.start()

    # send over the python code as a string
    run_unreal_python_commands(
        remote_exec,
        '\n'.join([
            f'unreal.EditorAssetLibrary.delete_directory(r"{directory_path}")',
        ]))

    if unreal_response is None or not unreal_response['success']:
        raise RuntimeError(f"delete_directory failed to delete {directory_path}")


def delete_asset(asset_path):
    """
    This function deletes an unreal asset from the project.

    :param str asset_path: The game path to the unreal project folder.
    """
    # start a connection to the engine that lets you send python strings
    remote_exec = RemoteExecution()
    remote_exec.start()

    # send over the python code as a string
    run_unreal_python_commands(
        remote_exec,
        '\n'.join([
            f'unreal.EditorAssetLibrary.delete_asset(r"{asset_path}")',
        ]))

    if unreal_response is None or not unreal_response['success']:
        raise RuntimeError(f"delete_asset failed to delete {asset_path}")


def is_unreal_running(attempts, ping):
    """
    This function suspends the program execution until unreal remote execution socket responds.

    :param int attempts : The number of times to try to make a connection.
    :param in ping: How many seconds to wait before trying to ping unreal.
    :return bool: Whether or not the editor responded.
    """
    logger.info('The Unreal Editor is launching... This might take a little while...')
    for attempt in range(1, attempts + 1):
        # start a connection to the engine that lets you send python strings
        remote_exec = RemoteExecution()
        remote_exec.start()

        try:
            # send over the python code as a string
            run_unreal_python_commands(remote_exec, commands="print('ping')")
            break
        except RuntimeError as error:
            logger.info(f'The Unreal Editor has not responded in {attempt*ping} seconds...')
            if attempt >= attempts:
                raise RuntimeError(error)
            time.sleep(ping)

    if unreal_response:
        return bool(unreal_response['success'])
    else:
        return False


def close_unreal(unreal_process):
    """
    This function closes the unreal editor.
    """
    if sys.platform == 'win32':
        # start a connection to the engine that lets you send python strings
        remote_exec = RemoteExecution()
        remote_exec.start()

        # send over the python code as a string
        run_unreal_python_commands(remote_exec, commands="import os; print(os.getpid())", attempts=5, ping=2)

        if unreal_response:
            if unreal_response['success']:
                process_id = int(unreal_response['output'][0]['output'])
                os.kill(process_id, signal.SIGTERM)

    # TODO needs to be tested on macOS
    else:
        unreal_process.terminate()


def launch_unreal():
    """
    This function launches a headless unreal editor and loads a project.
    """
    # the flags passed to the unreal editor
    flags = ['-unattended', '-nopause', '-nullrhi']

    # the relative path to the unreal project in the repo
    test_project = os.path.normpath(
        os.path.join(
            os.getcwd(),
            os.pardir,
            'unreal_projects',
            'test_project_01',
            'test_project_01.uproject'
        )
    )

    unreal_project = os.environ.get('UNREAL_PROJECT', test_project)

    # build the command to launch the unreal commandline according to each operating system
    # build the launch command for windows
    if sys.platform == 'win32':
        if sys.argv[-1].lower() == '--ci':
            unreal_executable = os.environ.get(
                'UNREAL_CMD_EXE',
                rf'C:\UnrealEngine\Engine\Binaries\Win64\{UNREAL}.exe'
            )
        else:
            unreal_executable = os.environ.get(
                'UNREAL_CMD_EXE',
                f'{UNREAL}'
            )

        command = rf'{unreal_executable} "{unreal_project}" {" ".join(flags)}'

        # run the unreal editor in a separate thread
        unreal_thread = threading.Thread(target=os.system, args=[command], daemon=True)
        unreal_thread.start()

    # TODO unreal macOS launch command needs to be tested
    else:
        if sys.argv[-1].lower() == '--ci':
            unreal_executable = os.environ.get(
                'UNREAL_CMD_EXE',
                f'/home/ue4/UnrealEngine/Engine/Binaries/Linux/{UNREAL}'
            )
        else:
            unreal_executable = os.environ.get(
                'UNREAL_CMD_EXE',
                f'{UNREAL}'
            )

        command = [unreal_executable, unreal_project] + flags

        unreal_process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT
        )

        return unreal_process
