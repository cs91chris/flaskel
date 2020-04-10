# import flask extension here
#
from .crypto import argon2
from .default import errors, logger, cors, builder, template, cfremote

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
