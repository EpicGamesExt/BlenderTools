# Copyright Epic Games, Inc. All Rights Reserved.

import os
import sys
from . import base_server
from .base_server import BaseRPCServerThread, BaseRPCServerManager


def execute_queued_calls():
    """
    Adds calls in the execution que that get picked up by blender app timer.
    :return float: The amount of time between timer calls.
    """
    try:
        base_server.execute_queued_calls()
    except Exception as error:
        sys.stderr.write(str(error))
    return 0.1


class BlenderRPCServerThread(BaseRPCServerThread):
    def thread_safe_call(self, callable_instance, *args):
        """
        Implementation of a thread safe call in Blender.
        """
        return lambda *args: base_server.run_in_main_thread(callable_instance, *args)


class RPCServer(BaseRPCServerManager):
    def __init__(self):
        """
        Initialize the blender rpc server, with its name and specific port.
        """
        super(RPCServer, self).__init__()
        self.name = 'BlenderRPCServer'
        self.port = int(os.environ.get('RPC_PORT', 9997))
        self.threaded_server_class = BlenderRPCServerThread

    def start_server_thread(self):
        """
        Starts the server thread.
        """
        import bpy
        bpy.app.timers.register(
            bpy.app.handlers.persistent(execute_queued_calls),
            persistent=True
        )
        super(RPCServer, self).start_server_thread()
