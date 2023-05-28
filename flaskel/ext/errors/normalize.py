import traceback
from datetime import datetime

from flask import current_app as cap
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt import PyJWTError
from werkzeug import exceptions, http
from werkzeug.routing import RequestRedirect

from flaskel.http.exceptions import Unauthorized

from .exception import ApiProblem


class BaseNormalize(object):
    def normalize(self, ex, **kwargs):
        """
        Child class must return super().normalize() in order to keep the chain of Mixins

        :param ex: input exception
        :return:
        """
        return ex


class RequestRedirectMixin(BaseNormalize):
    def normalize(self, ex, **kwargs):
        """

        :param ex:
        :return:
        """
        if isinstance(ex, RequestRedirect):
            location = dict(location=ex.new_url)
            ex.headers = location
            ex.response = location

        return super().normalize(ex)


class MethodNotAllowedMixin(BaseNormalize):
    def normalize(self, ex, **kwargs):
        """

        :param ex:
        :return:
        """
        if isinstance(ex, exceptions.MethodNotAllowed):
            if isinstance(ex.valid_methods, (list, tuple)):
                methods = ex.valid_methods
            else:
                methods = (ex.valid_methods,)
            try:
                ex.headers = dict(Allow=", ".join(methods))
                ex.response = dict(allowed=methods)
            except TypeError:  # pragma: no cover
                pass

        return super().normalize(ex)


class UnauthorizedMixin(BaseNormalize):
    def normalize(self, ex, **kwargs):
        """

        :param ex:
        :return:
        """

        def to_dict(item):
            item = dict(item)
            item["auth_type"] = item.pop("__auth_type__", None)
            return item

        if isinstance(ex, exceptions.Unauthorized):
            if ex.www_authenticate:
                ex.headers = {
                    "WWW-Authenticate": ", ".join([str(a) for a in ex.www_authenticate])
                }
                ex.response = dict(
                    authenticate=[to_dict(a) for a in ex.www_authenticate if a]
                )

        return super().normalize(ex)


class RequestedRangeNotSatisfiableMixin(BaseNormalize):
    def normalize(self, ex, **kwargs):
        """

        :param ex:
        :return:
        """
        if isinstance(ex, exceptions.RequestedRangeNotSatisfiable):
            if ex.length:
                unit = ex.units or "bytes"
                ex.headers = {"Content-Range": f"{unit} */{ex.length}"}
                ex.response = dict(units=unit, length=ex.length)

        return super().normalize(ex)


class RetryAfterMixin(BaseNormalize):
    def normalize(self, ex, **kwargs):
        """

        :param ex:
        :return:
        """
        if isinstance(ex, (exceptions.TooManyRequests, exceptions.ServiceUnavailable)):
            if ex.retry_after:
                retry = ex.retry_after
                if isinstance(retry, datetime):
                    retry = http.http_date(retry)

                ex.headers = {"Retry-After": str(retry)}
                ex.response = dict(retry_after=ex.retry_after)

        return super().normalize(ex)


class NormalizerMixin(BaseNormalize):
    class DumpEx:
        def __str__(self):
            return traceback.format_exc()

    def normalize(self, ex, exc_class=ApiProblem, **kwargs):
        """

        :param ex: Exception
        :param exc_class: overrides ApiProblem class
        :return: new Exception instance of HTTPException
        """
        ex = super().normalize(ex)

        if isinstance(ex, exc_class):
            return ex

        tb = self.DumpEx()
        if cap.config["DEBUG"]:
            mess = str(tb)  # pragma: no cover
        else:
            mess = cap.config["ERROR_DEFAULT_MSG"]

        _ex = exc_class(mess, **kwargs)

        if isinstance(ex, exceptions.HTTPException):
            _ex.code = ex.code
            _ex.description = ex.get_description()
            try:
                _ex.response = ex.response
            except AttributeError:
                _ex.response = None
            try:
                # noinspection PyUnresolvedReferences
                _ex.headers.update(ex.headers)
            except AttributeError:
                pass
        else:
            cap.logger.error("%s", tb)

        return _ex


class JWTErrorNormalizer(BaseNormalize):
    def normalize(self, ex, **kwargs):
        if isinstance(ex, (JWTExtendedException, PyJWTError)):
            response = {}
            if cap.debug:
                response["message"] = str(ex)
                response["exception"] = ex.__class__.__name__
            ex = Unauthorized(response=response)

        return super().normalize(ex)


class ErrorNormalizer(
    NormalizerMixin,
    MethodNotAllowedMixin,
    RequestRedirectMixin,
    UnauthorizedMixin,
    RequestedRangeNotSatisfiableMixin,
    RetryAfterMixin,
    JWTErrorNormalizer,
):
    """
    Default normalizer uses all mixins
    """
