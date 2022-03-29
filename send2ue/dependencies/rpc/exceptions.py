
class BaseRPCException(Exception):
    """
    Raised when a rpc class method is not authored as a static method.
    """
    def __init__(self, message=None, line_link=''):
        self.message = message + line_link
        super().__init__(self.message)


class InvalidClassMethod(BaseRPCException):
    """
    Raised when a rpc class method is not authored as a static method.
    """
    def __init__(self, cls, method, message=None, line_link=''):
        self.message = message

        if message is None:
            self.message = (
                f'\n  {cls.__name__}.{method.__name__} is not a static method. Please decorate with @staticmethod.'
            )
        BaseRPCException.__init__(self, self.message, line_link)


class InvalidTestCasePort(BaseRPCException):
    """
    Raised when a rpc test case class does not have a port defined.
    """
    def __init__(self, cls, message=None, line_link=''):
        self.message = message

        if message is None:
            self.message = f'\n  You must set {cls.__name__}.port to a supported RPC port.'
        BaseRPCException.__init__(self, self.message, line_link)


class InvalidKeyWordParameters(BaseRPCException):
    """
    Raised when a rpc function has key word arguments in its parameters.
    """
    def __init__(self, function, kwargs, message=None, line_link=''):
        self.message = message

        if message is None:
            self.message = (
                    f'\n  Keyword arguments "{kwargs}" were found on "{function.__name__}". The RPC client does not '
                    f'support key word arguments . Please change your code to use only arguments.'
                )
        BaseRPCException.__init__(self, self.message, line_link)


class UnsupportedArgumentType(BaseRPCException):
    """
    Raised when a rpc function's argument type is not supported.
    """
    def __init__(self, function, arg, supported_types, message=None, line_link=''):
        self.message = message

        if message is None:
            self.message = (
                f'\n  "{function.__name__}" has an argument of type "{arg.__class__.__name__}". The only types that are'
                f' supported by the RPC client are {[supported_type.__name__ for supported_type in supported_types]}.'
            )
        BaseRPCException.__init__(self, self.message, line_link)


class FileNotSavedOnDisk(BaseRPCException):
    """
    Raised when a rpc function is called in a context where it is not a saved file on disk.
    """
    def __init__(self, function, message=None):
        self.message = message

        if message is None:
            self.message = (
                f'\n  "{function.__name__}" is not being called from a saved file. The RPC client does not '
                f'support code that is not saved. Please save your code to a file on disk and re-run it.'
            )
        BaseRPCException.__init__(self, self.message)
