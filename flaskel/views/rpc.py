import functools
import inspect

from flask import request
from flask.views import View

import flaskel.http.rpc as rpc
from flaskel import cap, httpcode
from flaskel.ext import builder
from flaskel.utils.datastruct import ObjectDict


class JSONRPCView(View):
    version = '2.0'
    separator = '.'
    methods = ['POST']
    decorators = [builder.response('json')]

    def __init__(self, operations=None):
        """

        :param operations: a dict of jsonrpc operations like:
            {
                None: {
                    "action1": funct1,
                    "action2": funct2,
                    ...
                },
                "method1": {
                    "action1": funct1,
                    "action2": funct2,
                    ...
                },
                ...
            }
        """
        self.operations = operations or {}

    def _validate_payload(self):
        """

        :return:
        """
        payload = request.get_json(True)
        if not payload:
            raise rpc.RPCParseError() from None

        if 'jsonrpc' not in payload or \
                'method' not in payload:
            raise rpc.RPCInvalidRequest() from None

        if payload['jsonrpc'] != self.version:
            raise rpc.RPCInvalidRequest(f"jsonrpc version is {self.version}") from None

        return payload

    def _get_action(self, method):
        """

        :param method:
        :return:
        """
        m = method.split(self.separator)
        if len(m) > 1:
            op, action = m[0], self.separator.join(m[1:])
        else:
            op, action = None, m[0]

        try:
            return self.operations[op][action]
        except (IndexError, TypeError, KeyError) as exc:
            cap.logger.debug(exc)
            raise rpc.RPCMethodNotFound()

    def dispatch_request(self):
        """

        :return:
        """
        response = ObjectDict(dict(jsonrpc=self.version, id=None))

        try:
            payload = self._validate_payload()
            response.id = payload.get('id')

            action = self._get_action(payload['method'])
            response.result = action(**(payload.get('params') or {}))

            if 'id' not in payload:
                return None, httpcode.NO_CONTENT

        except rpc.RPCError as ex:
            response.error = ex.as_dict()
        except Exception as ex:
            cap.logger.exception(ex)
            mess = str(ex) if cap.config['DEBUG'] is True else None
            response.error = rpc.RPCInternalError(message=mess).as_dict()

        return response

    def load_from_object(self, obj):
        """

        :param obj:
        """
        for m in inspect.getmembers(obj, predicate=inspect.isroutine):
            if not m[0].startswith('_'):
                self.method(obj.__class__.__name__, m[0])(m[1])

    def method(self, name=None, operation=None):
        """

        :param name:
        :param operation:
        :return:
        """

        def _method(func):
            """

            :param func:
            :return:
            """
            nonlocal name
            name = name or func.__name__

            @functools.wraps(func)
            def wrapped():
                obj = {operation: func}
                if name not in self.operations:
                    self.operations[name] = obj
                else:
                    self.operations[name].update(obj)

            return wrapped()

        return _method

    def register(self, app, name, url, **kwargs):
        """

        :param app: Flask or Blueprint instance
        :param name:
        :param url:
        """
        view_func = self.__class__.as_view(name, self.operations, **kwargs)

        url = url.rstrip('/')
        if not url.startswith('/'):
            url = f"/{url}"

        app.add_url_rule(url, view_func=view_func, methods=self.methods)
