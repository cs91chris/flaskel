from flaskel.utils.datastruct import ObjectDict
from . import httpcode


class RPCError(Exception):
    def __init__(self, code, message, data=None):
        """

        :param code:
        :param message:
        :param data:
        """
        super().__init__(code, message)
        self.code = code
        self.message = message
        self.data = data

    def as_dict(self):
        """

        :return:
        """
        return ObjectDict(code=self.code, message=self.message, data=self.data)


class RPCParseError(RPCError):
    def __init__(self, message="Invalid JSON was received by the server", data=None):
        """

        :param message:
        :param data:
        """
        super().__init__(-32700, message, data)


class RPCInvalidRequest(RPCError):
    def __init__(
        self,
        message="The JSON sent is not a valid Request object",
        data=None,
        req_id=None,
    ):
        """

        :param message:
        :param data:
        """
        super().__init__(-32600, message, data)
        self.req_id = req_id


class RPCMethodNotFound(RPCError):
    def __init__(
        self, message="The method does not exist or is not available", data=None
    ):
        """

        :param message:
        :param data:
        """
        super().__init__(-32601, message, data)


class RPCInvalidParams(RPCError):
    def __init__(self, message="Invalid method parameter(s)", data=None):
        """

        :param message:
        :param data:
        """
        super().__init__(-32602, message, data)


class RPCInternalError(RPCError):
    def __init__(self, message="Internal JSON-RPC error", data=None):
        """

        :param message:
        :param data:
        """
        super().__init__(-32603, message, data)


def rpc_error_to_httpcode(error_code: int) -> int:
    """

    :param error_code:
    :return:
    """
    if error_code == RPCParseError().code:
        return httpcode.BAD_REQUEST
    if error_code == RPCInvalidRequest().code:
        return httpcode.BAD_REQUEST
    if error_code == RPCMethodNotFound().code:
        return httpcode.NOT_FOUND
    if error_code == RPCInvalidParams().code:
        return httpcode.UNPROCESSABLE_ENTITY

    return httpcode.INTERNAL_SERVER_ERROR
