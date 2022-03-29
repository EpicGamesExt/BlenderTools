import inspect

from .exceptions import (
    InvalidClassMethod,
    InvalidTestCasePort,
    InvalidKeyWordParameters,
    UnsupportedArgumentType,
    FileNotSavedOnDisk,
)


def get_source_file_path(function):
    """
    Gets the full path to the source code.

    :param callable function: A callable.
    :return str: A file path.
    """
    client_module = inspect.getmodule(function)
    return client_module.__file__


def get_line_link(function):
    """
    Gets the line number of a function.

    :param callable function: A callable.
    :return int: The line number
    """
    lines, line_number = inspect.getsourcelines(function)
    file_path = get_source_file_path(function)
    return f'  File "{file_path}", line {line_number}'


def validate_arguments(function, args):
    """
    Validates arguments to ensure they are a supported type.

    :param callable function: A function reference.
    :param tuple(Any) args: A list of arguments.
    """
    supported_types = [str, int, float, tuple, list, dict, bool]
    line_link = get_line_link(function)
    for arg in args:
        if arg is None:
            continue

        if type(arg) not in supported_types:
            raise UnsupportedArgumentType(function, arg, supported_types, line_link=line_link)


def validate_test_case_class(cls):
    """
    This is use to validate a subclass of RPCTestCase. While building your test
    suite you can call this method on each class preemptively to validate that it
    was defined correctly.

    :param RPCTestCase cls: A class.
    :param str file_path: Optionally, a file path to the test case can be passed to give
    further context into where the error is occurring.
    """
    line_link = get_line_link(cls)
    if not cls.__dict__.get('port'):
        raise InvalidTestCasePort(cls, line_link=line_link)

    for attribute, method in cls.__dict__.items():
        if callable(method) and not isinstance(method, staticmethod):
            if method.__name__.startswith('test'):
                raise InvalidClassMethod(cls, method, line_link=line_link)


def validate_class_method(cls, method):
    """
    Validates a method on a class.

    :param Any cls: A class.
    :param callable method: A callable.
    """
    if callable(method) and not isinstance(method, staticmethod):
        line_link = get_line_link(method)
        raise InvalidClassMethod(cls, method, line_link=line_link)


def validate_key_word_parameters(function, kwargs):
    """
    Validates a method on a class.

    :param callable function: A callable.
    :param dict kwargs: A dictionary of key word arguments.
    """
    if kwargs:
        line_link = get_line_link(function)
        raise InvalidKeyWordParameters(function, kwargs, line_link=line_link)


def validate_file_is_saved(function):
    """
    Validates that the file that the function is from is saved on disk.

    :param callable function: A callable.
    """
    try:
        inspect.getsourcelines(function)
    except OSError:
        raise FileNotSavedOnDisk(function)
