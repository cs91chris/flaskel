# import flask extension here
#
from .default import errors
from .default import logger
from .default import cors
from .default import builder
from .default import template
from .default import cfremote

from .crypto import argon2


EXTENSIONS = (
    # (extension, parameters)
    (logger,),
    (argon2,),
    (template,),
    (cfremote,),
    (builder,),
    (errors, {
        'response': builder.on_accept()
    }),
)
