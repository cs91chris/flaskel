from flask import current_app as cap
from flask_errors_handler import DefaultNormalizer
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt import PyJWTError

from flaskel.http.exceptions import Unauthorized

jwt_errors = (JWTExtendedException, PyJWTError)


class ErrorNormalizer(DefaultNormalizer):
    def normalize(self, ex, *_, **__):
        if isinstance(ex, jwt_errors):
            response = {}
            if cap.debug:
                response["message"] = str(ex)
                response["exception"] = ex.__class__.__name__
            ex = Unauthorized(response=response)

        return super().normalize(ex)
