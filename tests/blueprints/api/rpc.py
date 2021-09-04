from flaskel.http import rpc


# noinspection PyPep8Naming,PyMethodMayBeStatic,PyUnusedLocal pylint: disable=invalid-name,no-self-use
class MyJsonRPC:
    def testAction1(self, **__):
        return {"action1": True}

    def testAction2(self, **__):
        return {"action2": True}

    def testInvalidParams(self, **kwargs):
        if kwargs.get("param") != "testparam":
            raise rpc.RPCInvalidParams()

    def testInternalError(self):
        raise ValueError
