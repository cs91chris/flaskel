from .default import cors, errors, logger, cors, builder, template, cfremote, argon2

EXTENSIONS = (
    # (extension, parameters: dict)
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
