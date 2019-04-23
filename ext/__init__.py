# import flask extension here
#
from .default import errors
from .default import logger
from .default import cors

from .crypto import argon2


EXTENSIONS = (
    # (extension, parameters)
    (logger,),
    (errors,),
    (argon2,),
)
