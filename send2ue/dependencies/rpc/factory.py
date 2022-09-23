import os
import re
import sys
import logging
import types
import inspect
import textwrap
import unittest
from xmlrpc.client import Fault

from .client import RPCClient
from .validations import (
    validate_key_word_parameters,
    validate_class_method,
    get_source_file_path,
    get_line_link,
    validate_arguments,
    validate_file_is_saved,
)

logger = logging.getLogger(__package__)


class RPCFactory:
    def __init__(self, rpc_client, remap_pairs=None, default_imports=None):
        self.rpc_client = rpc_client
        self.file_path = None
        self.remap_pairs = remap_pairs
        self.default_imports = default_imports or []

    @staticmethod
    def _get_docstring(code, function_name):
        """
        Gets the docstring value from the functions code.

        :param list code: A list of code lines.
        :param str function_name: The name of the function.
        :returns: The docstring text.
        :rtype: str
        """
        # run the function code
        exec('\n'.join(code))
        # get the function from the locals
        function_instance = locals().copy().get(function_name)
        # get the doc strings from the function
        return function_instance.__doc__

    @staticmethod
    def _save_execution_history(code, function, args):
        """
        Saves out the executed code to a file.

        :param list code: A list of code lines.
        :param callable function: A function.
        :param list args: A list of function arguments.
        """
        history_file_path = os.environ.get('RPC_EXECUTION_HISTORY_FILE')

        if history_file_path and os.path.exists(os.path.dirname(history_file_path)):
            file_size = 0
            if os.path.exists(history_file_path):
                file_size = os.path.getsize(history_file_path)

            with open(history_file_path, 'a') as history_file:
                # add the import for SourceFileLoader if the file is empty
                if file_size == 0:
                    history_file.write('from importlib.machinery import SourceFileLoader\n')

                # space out the functions
                history_file.write(f'\n\n')

                for line in code:
                    history_file.write(f'{line}\n')

                # convert the args to strings
                formatted_args = []
                for arg in args:
                    if isinstance(arg, str):
                        formatted_args.append(f'r"{arg}"')
                    else:
                        formatted_args.append(str(arg))

                # write the call with the arg values
                params = ", ".join(formatted_args) if formatted_args else ''
                history_file.write(f'{function.__name__}({params})\n')

    def _get_callstack_references(self, code, function):
        """
        Gets all references for the given code.

        :param list[str] code: The code of the callable.
        :param callable function: A callable.
        :return str: The new code of the callable with all its references added.
        """
        import_code = self.default_imports

        client_module = inspect.getmodule(function)
        self.file_path = get_source_file_path(function)

        # if a list of remap pairs have been set, the file path will be remapped to the new server location
        # Note: The is useful when the server and client are not on the same machine.
        server_module_path = self.file_path
        for client_path_root, matching_server_path_root in self.remap_pairs or []:
            if self.file_path.startswith(client_path_root):
                server_module_path = os.path.join(
                    matching_server_path_root,
                    self.file_path.replace(client_path_root, '').replace(os.sep, '/').strip('/')
                )
                break

        for key in dir(client_module):
            for line_number, line in enumerate(code):
                if line.startswith('def '):
                    continue

                if key in re.split('\.|\(| ', line.strip()):
                    if os.path.basename(self.file_path) == '__init__.py':
                        base_name = os.path.basename(os.path.dirname(self.file_path))
                    else:
                        base_name = os.path.basename(self.file_path)

                    module_name, file_extension = os.path.splitext(base_name)

                    # add the source file to the import code
                    source_import_code = f'{module_name} = SourceFileLoader("{module_name}", r"{server_module_path}").load_module()'
                    if source_import_code not in import_code:
                        import_code.append(source_import_code)

                    # relatively import the module from the source file
                    relative_import_code = f'from {module_name} import {key}'
                    if relative_import_code not in import_code:
                        import_code.append(relative_import_code)

                    break

        return textwrap.indent('\n'.join(import_code), ' ' * 4)

    def _get_code(self, function):
        """
        Gets the code from a callable.

        :param callable function: A callable.
        :return str: The code of the callable.
        """
        code = textwrap.dedent(inspect.getsource(function)).split('\n')
        code = [line for line in code if not line.startswith(('@', '#'))]

        # get the docstring from the code
        doc_string = self._get_docstring(code, function.__name__)

        # get import code and insert them inside the function
        import_code = self._get_callstack_references(code, function)
        code.insert(1, import_code)

        # remove the doc string
        if doc_string:
            code = '\n'.join(code).replace(doc_string, '')
            code = [line for line in code.split('\n') if not all([char == '"' or char == "'" for char in line.strip()])]

        return code

    def _register(self, function):
        """
        Registers a given callable with the server.

        :param  callable function: A callable.
        :return: The code of the function.
        :rtype: list
        """
        code = self._get_code(function)
        try:
            # if additional paths are explicitly set, then use them. This is useful with the client is on another
            # machine and the python paths are different
            additional_paths = list(filter(None, os.environ.get('RPC_ADDITIONAL_PYTHON_PATHS', '').split(',')))

            if not additional_paths:
                # otherwise use the current system path
                additional_paths = sys.path

            response = self.rpc_client.proxy.add_new_callable(
                function.__name__, '\n'.join(code),
                additional_paths
            )
            if os.environ.get('RPC_DEBUG'):
                logger.debug(response)

        except ConnectionRefusedError:
            server_name = os.environ.get(f'RPC_SERVER_{self.rpc_client.port}', self.rpc_client.port)
            raise ConnectionRefusedError(f'No connection could be made with "{server_name}"')

        return code

    def run_function_remotely(self, function, args):
        """
        Handles running the given function on remotely.

        :param callable function: A function reference.
        :param tuple(Any) args: The function's arguments.
        :return callable: A remote callable.
        """
        validate_arguments(function, args)

        # get the remote function instance
        code = self._register(function)
        remote_function = getattr(self.rpc_client.proxy, function.__name__)
        self._save_execution_history(code, function, args)

        current_frame = inspect.currentframe()
        outer_frame_info = inspect.getouterframes(current_frame)
        # step back 2 frames in the callstack
        caller_frame = outer_frame_info[2][0]
        # create a trace back that is relevant to the remote code rather than the code transporting it
        call_traceback = types.TracebackType(None, caller_frame, caller_frame.f_lasti, caller_frame.f_lineno)
        # call the remote function
        if not self.rpc_client.marshall_exceptions:
            # if exceptions are not marshalled then receive the default Fault
            return remote_function(*args)

        # otherwise catch them and add a line link to them
        try:
            return remote_function(*args)
        except Exception as exception:
            stack_trace = str(exception) + get_line_link(function)
            if isinstance(exception, Fault):
                raise Fault(exception.faultCode, exception.faultString)
            raise exception.__class__(stack_trace).with_traceback(call_traceback)


def remote_call(port, default_imports=None, remap_pairs=None):
    """
    A decorator that makes this function run remotely.

    :param Enum port: The name of the port application i.e. maya, blender, unreal.
    :param list[str] default_imports: A list of import commands that include modules in every call.
    :param list(tuple) remap_pairs: A list of tuples with first value being the client file path root and the
    second being the matching server path root. This can be useful if the client and server are on two different file
    systems and the root of the import paths need to be dynamically replaced.
    """
    def decorator(function):
        def wrapper(*args, **kwargs):
            validate_file_is_saved(function)
            validate_key_word_parameters(function, kwargs)
            rpc_factory = RPCFactory(
                rpc_client=RPCClient(port),
                remap_pairs=remap_pairs,
                default_imports=default_imports
            )
            return rpc_factory.run_function_remotely(function, args)
        return wrapper
    return decorator


def remote_class(decorator):
    """
    A decorator that makes this class run remotely.

    :param remote_call decorator: The remote call decorator.
    :return: A decorated class.
    """
    def decorate(cls):
        for attribute, value in cls.__dict__.items():
            validate_class_method(cls, value)
            if callable(getattr(cls, attribute)):
                setattr(cls, attribute, decorator(getattr(cls, attribute)))
        return cls
    return decorate


class RPCTestCase(unittest.TestCase):
    """
    Subclasses unittest.TestCase to implement a RPC compatible TestCase.
    """
    port = None
    remap_pairs = None
    default_imports = None

    @classmethod
    def run_remotely(cls, method, args):
        """
        Run the given method remotely.

        :param callable method: A method to wrap.
        """
        default_imports = cls.__dict__.get('default_imports', None)
        port = cls.__dict__.get('port', None)
        remap_pairs = cls.__dict__.get('remap_pairs', None)
        rpc_factory = RPCFactory(
            rpc_client=RPCClient(port),
            default_imports=default_imports,
            remap_pairs=remap_pairs
        )
        return rpc_factory.run_function_remotely(method, args)

    def _callSetUp(self):
        """
        Overrides the TestCase._callSetUp method by passing it to be run remotely.
        Notice None is passed as an argument instead of self. This is because only static methods
        are allowed by the RPCClient.
        """
        self.run_remotely(self.setUp, [None])

    def _callTearDown(self):
        """
        Overrides the TestCase._callTearDown method by passing it to be run remotely.
        Notice None is passed as an argument instead of self. This is because only static methods
        are allowed by the RPCClient.
        """
        # notice None is passed as an argument instead of self so self can't be used
        self.run_remotely(self.tearDown, [None])

    def _callTestMethod(self, method):
        """
        Overrides the TestCase._callTestMethod method by capturing the test case method that would be run and then
        passing it to be run remotely. Notice no arguments are passed. This is because only static methods
        are allowed by the RPCClient.

        :param callable method: A method from the test case.
        """
        self.run_remotely(method, [])
