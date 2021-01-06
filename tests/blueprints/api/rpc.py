from flaskel.http import rpc


# noinspection PyPep8Naming,PyMethodMayBeStatic,PyUnusedLocal
class MyJsonRPC:
    def testAction1(self, **kwargs):
        return {
            "action1": True
        }

    def testAction2(self, **kwargs):
        return {
            "action2": True
        }

    def testInvalidParams(self, **kwargs):
        if kwargs.get('param') != 'testparam':
            raise rpc.RPCInvalidParams()

    def testInternalError(self):
        raise ValueError
