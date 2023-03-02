import os
import re
import logging
import inspect
from xmlrpc.client import (
    ServerProxy,
    Unmarshaller,
    Transport,
    ExpatParser,
    Fault,
    ResponseError
)
logger = logging.getLogger(__package__)


class RPCUnmarshaller(Unmarshaller):
    def __init__(self, *args, **kwargs):
        Unmarshaller.__init__(self, *args, **kwargs)
        self.error_pattern = re.compile(r'(?P<exception>[^:]*):(?P<exception_message>.*$)')
        self.builtin_exceptions = self._get_built_in_exceptions()

    @staticmethod
    def _get_built_in_exceptions():
        """
        Gets a list of the built-in exception classes in python.

        :return list[BaseException] A list of the built in exception classes in python:
        """
        builtin_exceptions = []
        for builtin_name, builtin_class in globals().get('__builtins__').items():
            if builtin_class and inspect.isclass(builtin_class) and issubclass(builtin_class, BaseException):
                builtin_exceptions.append(builtin_class)

        return builtin_exceptions

    def close(self):
        """
        Override so we redefine the unmarshaller.

        :return tuple: A tuple of marshallables.
        """
        if self._type is None or self._marks:
            raise ResponseError()

        if self._type == 'fault':
            marshallables = self._stack[0]
            match = self.error_pattern.match(marshallables.get('faultString', ''))
            if match:
                exception_name = match.group('exception').strip("<class '").strip("'>")
                exception_message = match.group('exception_message')

                if exception_name:
                    for exception in self.builtin_exceptions:
                        if exception.__name__ == exception_name:
                            raise exception(exception_message)

            # if all else fails just raise the fault
            raise Fault(**marshallables)
        return tuple(self._stack)


class RPCTransport(Transport):
    def getparser(self):
        """
        Override so we can redefine our transport to use its own custom unmarshaller.

        :return tuple(ExpatParser, RPCUnmarshaller): The parser and unmarshaller instances.
        """
        unmarshaller = RPCUnmarshaller()
        parser = ExpatParser(unmarshaller)
        return parser, unmarshaller


class RPCServerProxy(ServerProxy):
    auth_key = None

    def __init__(self, *args, **kwargs):
        """
        Override so we can redefine the ServerProxy to use our custom transport.
        """
        kwargs['transport'] = RPCTransport()
        ServerProxy.__init__(self, *args, **kwargs)


class RPCClient:
    def __init__(self, port, marshall_exceptions=True):
        """
        Initializes the rpc client.

        :param int port: A port number the client should connect to.
        :param bool marshall_exceptions: Whether the exceptions should be marshalled.
        """
        server_ip = os.environ.get('RPC_SERVER_IP', '127.0.0.1')

        self.proxy = RPCServerProxy(
            f"http://{server_ip}:{port}",
            allow_none=True,
        )
        self.marshall_exceptions = marshall_exceptions
        self.port = port
