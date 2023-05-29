import traceback
from datetime import datetime

from flask import current_app as cap
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt import PyJWTError
from vbcore.datastruct import ObjectDict
from vbcore.http.headers import HeaderEnum
from werkzeug import exceptions, http
from werkzeug.routing import RequestRedirect

from flaskel.http.exceptions import Unauthorized

from .exception import ApiProblem


class BaseNormalize:
    def normalize(self, ex, **kwargs):
        """
        Child class must return super().normalize() in order to keep the chain of Mixins
        """
        if isinstance(ex, ApiProblem):
            return ex

        if cap.config["DEBUG"]:
            mess = str(traceback.format_exc())  # pragma: no cover
        else:
            mess = cap.config["ERROR_DEFAULT_MSG"]

        _ex = ApiProblem(mess, **kwargs)

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
            cap.logger.error("%s", traceback.format_exc())

        return _ex


class RequestRedirectMixin(BaseNormalize):
    def normalize(self, ex, **kwargs):
        if isinstance(ex, RequestRedirect):
            location = {"location": ex.new_url}
            ex.headers = location
            ex.response = location

        return super().normalize(ex)


class MethodNotAllowedMixin(BaseNormalize):
    def normalize(self, ex, **kwargs):
        if isinstance(ex, exceptions.MethodNotAllowed):
            if isinstance(ex.valid_methods, (list, tuple)):
                methods = ex.valid_methods
            else:
                methods = (ex.valid_methods,)
            try:
                ex.headers = ObjectDict(Allow=", ".join(methods))
                ex.response = ObjectDict(allowed=methods)
            except TypeError:  # pragma: no cover
                pass

        return super().normalize(ex)


class UnauthorizedMixin(BaseNormalize):
    def normalize(self, ex, **kwargs):
        if isinstance(ex, exceptions.Unauthorized):
            if ex.www_authenticate:
                ex.headers = {
                    HeaderEnum.WWW_AUTHENTICATE: ", ".join(
                        [auth.to_header() for auth in ex.www_authenticate]
                    )
                }
                ex.response = ObjectDict(
                    authenticate=[
                        {"auth_type": auth.type, **auth.parameters}
                        for auth in ex.www_authenticate
                        if auth
                    ]
                )

        return super().normalize(ex)


class RequestedRangeNotSatisfiableMixin(BaseNormalize):
    def normalize(self, ex, **kwargs):
        if isinstance(ex, exceptions.RequestedRangeNotSatisfiable):
            if ex.length:
                unit = ex.units or "bytes"
                ex.headers = {HeaderEnum.CONTENT_RANGE: f"{unit} */{ex.length}"}
                ex.response = ObjectDict(units=unit, length=ex.length)

        return super().normalize(ex)


class RetryAfterMixin(BaseNormalize):
    def normalize(self, ex, **kwargs):
        if isinstance(ex, (exceptions.TooManyRequests, exceptions.ServiceUnavailable)):
            if ex.retry_after:
                retry = ex.retry_after
                if isinstance(retry, datetime):
                    retry = http.http_date(retry)

                ex.headers = {HeaderEnum.RETRY_AFTER: str(retry)}
                ex.response = ObjectDict(retry_after=ex.retry_after)

        return super().normalize(ex)


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
