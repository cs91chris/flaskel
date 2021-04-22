from flask import current_app as cap
from flask_errors_handler import DefaultNormalizer, ErrorHandler
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt import PyJWTError

from flaskel.http.exceptions import Unauthorized


class ErrorNormalizer(DefaultNormalizer):
    def normalize(self, ex, *args, **kwargs):
        if isinstance(ex, (JWTExtendedException, PyJWTError)):
            response = dict()
            if cap.debug:
                response['message'] = str(ex)
                response['exception'] = ex.__class__.__name__
            ex = Unauthorized(response=response)

        return super().normalize(ex)


error_handler = ErrorHandler(normalizer=ErrorNormalizer())
