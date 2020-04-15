from flaskel.ext.crypto import argon2
from flaskel.ext.default import errors, logger, cors, builder, template, cfremote

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
