import os
from .base_server import BaseRPCServerManager


class RPCServer(BaseRPCServerManager):
    def __init__(self):
        """
        Initialize the blender rpc server, with its name and specific port.
        """
        super(RPCServer, self).__init__()
        self.name = 'RPCServer'
        self.port = int(os.environ.get('RPC_PORT', 9998))
