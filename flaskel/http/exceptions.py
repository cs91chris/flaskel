import inspect
import sys

import flask
from werkzeug import exceptions

from flaskel.utils.datastruct import ConfigProxy
from . import httpcode


class HTTPExceptionMixin:
    description = ""
    config = ConfigProxy("HTTP_EXCEPTIONS")
    lang_key = ConfigProxy("HTTP_EXCEPTIONS.LANG_KEY")
    lang_default = ConfigProxy("HTTP_EXCEPTIONS.LANG_DEFAULT")

    # noinspection PyUnusedLocal
    def get_description(self, environ=None, scope=None) -> str:  # pylint: disable=W0613
        lang = self.config.get(flask.g.get(self.lang_key.get() or "lang"))
        lang = lang or self.config.get(self.lang_default.get()) or {}
        desc = lang.get(self.description)
        desc = desc or self.config.get(self.description)
        desc = desc or self.description.lower().replace("_", " ")
        return desc or "unhandled error"


class BadRequest(HTTPExceptionMixin, exceptions.BadRequest):
    code = httpcode.BAD_REQUEST
    description = "BAD_REQUEST"


class Unauthorized(HTTPExceptionMixin, exceptions.Unauthorized):
    code = httpcode.UNAUTHORIZED
    description = "UNAUTHORIZED"


class PaymentRequired(HTTPExceptionMixin, exceptions.HTTPException):
    code = httpcode.PAYMENT_REQUIRED
    description = "PAYMENT_REQUIRED"


class Forbidden(HTTPExceptionMixin, exceptions.Forbidden):
    code = httpcode.FORBIDDEN
    description = "FORBIDDEN"


class NotFound(HTTPExceptionMixin, exceptions.NotFound):
    code = httpcode.NOT_FOUND
    description = "NOT_FOUND"


class MethodNotAllowed(HTTPExceptionMixin, exceptions.MethodNotAllowed):
    code = httpcode.METHOD_NOT_ALLOWED
    description = "METHOD_NOT_ALLOWED"


class NotAcceptable(HTTPExceptionMixin, exceptions.NotAcceptable):
    code = httpcode.NOT_ACCEPTABLE
    description = "NOT_ACCEPTABLE"


class ProxyAuthenticationRequired(HTTPExceptionMixin, exceptions.HTTPException):
    code = httpcode.PROXY_AUTHENTICATION_REQUIRED
    description = "PROXY_AUTHENTICATION_REQUIRED"


class RequestTimeout(HTTPExceptionMixin, exceptions.RequestTimeout):
    code = httpcode.REQUEST_TIMEOUT
    description = "REQUEST_TIMEOUT"


class Conflict(HTTPExceptionMixin, exceptions.Conflict):
    code = httpcode.CONFLICT
    description = "CONFLICT"


class Gone(HTTPExceptionMixin, exceptions.Gone):
    code = httpcode.GONE
    description = "GONE"


class LengthRequired(HTTPExceptionMixin, exceptions.LengthRequired):
    code = httpcode.LENGTH_REQUIRED
    description = "LENGTH_REQUIRED"


class PreconditionFailed(HTTPExceptionMixin, exceptions.PreconditionFailed):
    code = httpcode.PRECONDITION_FAILED
    description = "PRECONDITION_FAILED"


class RequestEntityTooLarge(HTTPExceptionMixin, exceptions.RequestEntityTooLarge):
    code = httpcode.REQUEST_ENTITY_TOO_LARGE
    description = "REQUEST_ENTITY_TOO_LARGE"


class RequestURITooLarge(HTTPExceptionMixin, exceptions.RequestURITooLarge):
    code = httpcode.REQUEST_URI_TOO_LONG
    description = "REQUEST_URI_TOO_LONG"


class UnsupportedMediaType(HTTPExceptionMixin, exceptions.UnsupportedMediaType):
    code = httpcode.UNSUPPORTED_MEDIA_TYPE
    description = "UNSUPPORTED_MEDIA_TYPE"


class RequestedRangeNotSatisfiable(
    HTTPExceptionMixin, exceptions.RequestedRangeNotSatisfiable
):
    code = httpcode.RANGE_NOT_SATISFIABLE
    description = "RANGE_NOT_SATISFIABLE"


class ExpectationFailed(HTTPExceptionMixin, exceptions.ExpectationFailed):
    code = httpcode.EXPECTATION_FAILED
    description = "EXPECTATION_FAILED"


class MisdirectedRequest(HTTPExceptionMixin, exceptions.HTTPException):
    code = httpcode.MISDIRECTED_REQUEST
    description = "MISDIRECTED_REQUEST"


class UnprocessableEntity(HTTPExceptionMixin, exceptions.UnprocessableEntity):
    code = httpcode.UNPROCESSABLE_ENTITY
    description = "UNPROCESSABLE_ENTITY"


class Locked(HTTPExceptionMixin, exceptions.Locked):
    code = httpcode.LOCKED
    description = "LOCKED"


class FailedDependency(HTTPExceptionMixin, exceptions.FailedDependency):
    code = httpcode.FAILED_DEPENDENCY
    description = "FAILED_DEPENDENCY"


class TooEarly(HTTPExceptionMixin, exceptions.HTTPException):
    code = httpcode.TOO_EARLY
    description = "TOO_EARLY"


class UpgradeRequired(HTTPExceptionMixin, exceptions.HTTPException):
    code = httpcode.UPGRADE_REQUIRED
    description = "UPGRADE_REQUIRED"


class PreconditionRequired(HTTPExceptionMixin, exceptions.PreconditionRequired):
    code = httpcode.PRECONDITION_REQUIRED
    description = "PRECONDITION_REQUIRED"


class TooManyRequests(HTTPExceptionMixin, exceptions.TooManyRequests):
    code = httpcode.TOO_MANY_REQUESTS
    description = "TOO_MANY_REQUESTS"


class RequestHeaderFieldsTooLarge(
    HTTPExceptionMixin, exceptions.RequestHeaderFieldsTooLarge
):
    code = httpcode.REQUEST_HEADER_FIELDS_TOO_LARGE
    description = "REQUEST_HEADER_FIELDS_TOO_LARGE"


class NoResponse(HTTPExceptionMixin, exceptions.HTTPException):
    code = httpcode.NO_RESPONSE
    description = "NO_RESPONSE"


class UnavailableForLegalReasons(
    HTTPExceptionMixin, exceptions.UnavailableForLegalReasons
):
    code = httpcode.UNAVAILABLE_FOR_LEGAL_REASON
    description = "UNAVAILABLE_FOR_LEGAL_REASON"


class InternalServerError(HTTPExceptionMixin, exceptions.InternalServerError):
    code = httpcode.INTERNAL_SERVER_ERROR
    description = "INTERNAL_SERVER_ERROR"


# noinspection PyShadowingBuiltins
class NotImplemented(
    HTTPExceptionMixin, exceptions.NotImplemented
):  # pylint: disable=W0622
    code = httpcode.NOT_IMPLEMENTED
    description = "NOT_IMPLEMENTED"


class BadGateway(HTTPExceptionMixin, exceptions.BadGateway):
    code = httpcode.BAD_GATEWAY
    description = "BAD_GATEWAY"


class ServiceUnavailable(HTTPExceptionMixin, exceptions.ServiceUnavailable):
    code = httpcode.SERVICE_UNAVAILABLE
    description = "SERVICE_UNAVAILABLE"


class GatewayTimeout(HTTPExceptionMixin, exceptions.GatewayTimeout):
    code = httpcode.GATEWAY_TIMEOUT
    description = "GATEWAY_TIMEOUT"


class HTTPVersionNotSupported(HTTPExceptionMixin, exceptions.HTTPVersionNotSupported):
    code = httpcode.HTTP_VERSION_NOT_SUPPORTED
    description = "HTTP_VERSION_NOT_SUPPORTED"


class InsufficientStorage(HTTPExceptionMixin, exceptions.HTTPException):
    code = httpcode.INSUFFICIENT_STORAGE
    description = "INSUFFICIENT_STORAGE"


class LoopDetected(HTTPExceptionMixin, exceptions.HTTPException):
    code = httpcode.LOOP_DETECTED
    description = "LOOP_DETECTED"


class BandwidthLimit(HTTPExceptionMixin, exceptions.HTTPException):
    code = httpcode.BANDWIDTH_LIMIT
    description = "BANDWIDTH_LIMIT"


class NotExtended(HTTPExceptionMixin, exceptions.HTTPException):
    code = httpcode.NOT_EXTENDED
    description = "NOT_EXTENDED"


class NetworkAuthenticationRequired(HTTPExceptionMixin, exceptions.HTTPException):
    code = httpcode.NETWORK_AUTHENTICATION_REQUIRED
    description = "NETWORK_AUTHENTICATION_REQUIRED"


class UnknownError(HTTPExceptionMixin, exceptions.HTTPException):
    code = httpcode.UNKNOWN_ERROR
    description = "UNKNOWN_ERROR"


_errors = inspect.getmembers(
    sys.modules[__name__],
    lambda c: inspect.isclass(c) and issubclass(c, exceptions.HTTPException),
)

# until a better solution are found
setattr(flask, "abort", exceptions.Aborter(mapping={e.code: e for _, e in _errors}))
