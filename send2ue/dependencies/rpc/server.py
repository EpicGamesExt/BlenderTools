import os
import sys
sys.path.append(os.path.dirname(__file__))

from base_server import BaseRPCServerManager


class RPCServer(BaseRPCServerManager):
    def __init__(self):
        """
        Initialize the blender rpc server, with its name and specific port.
        """
        super(RPCServer, self).__init__()
        self.name = 'RPCServer'
        self.port = int(os.environ.get('RPC_PORT', 9998))


if __name__ == '__main__':
    rpc_server = RPCServer()
    rpc_server.start(threaded=False)
