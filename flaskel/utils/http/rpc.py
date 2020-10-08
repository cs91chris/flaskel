class RPCError(Exception):
    def __init__(self, code, message, data=None):
        """

        :param code:
        :param message:
        :param data:
        """
        self.code = code
        self.message = message
        self.data = data

    def as_dict(self):
        """

        :return:
        """
        return dict(
            code=self.code,
            message=self.message,
            data=self.data
        )


class RPCParseError(RPCError):
    def __init__(self, message=None, data=None):
        """

        :param message:
        :param data:
        """
        super().__init__(
            -32700,
            message or 'Invalid JSON was received by the server',
            data
        )


class RPCInvalidRequest(RPCError):
    def __init__(self, message=None, data=None):
        """

        :param message:
        :param data:
        """
        super().__init__(
            -32600,
            message or 'The JSON sent is not a valid Request object',
            data
        )


class RPCMethodNotFound(RPCError):
    def __init__(self, message=None, data=None):
        """

        :param message:
        :param data:
        """
        super().__init__(
            -32601,
            message or 'The method does not exist or is not available',
            data
        )


class RPCInvalidParams(RPCError):
    def __init__(self, message=None, data=None):
        """

        :param message:
        :param data:
        """
        super().__init__(
            -32602,
            message or 'Invalid method parameter(s)',
            data
        )


class RPCInternalError(RPCError):
    def __init__(self, message=None, data=None):
        """

        :param message:
        :param data:
        """
        super().__init__(
            -32603,
            message or 'Internal JSON-RPC error',
            data
        )
