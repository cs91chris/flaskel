from .default import cors, errors, logger, cors, builder, template, cfremote, argon2

EXTENSIONS = (
    # (extension, parameters)
    (logger,),
    (cors,),
    (argon2,),
    (template,),
    (cfremote,),
    (builder,),
    (errors, {
        'response': builder.on_accept()
    }),
)
