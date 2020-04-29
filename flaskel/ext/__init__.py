from .default import (
    cors,
    errors,
    logger,
    builder,
    template,
    cfremote,
    argon2,
)

EXTENSIONS = (
    # (extension, parameters: dict)
    (logger,),
    (cors,),
    (argon2,),
    (template,),
    (cfremote,),
    (builder,),
    (errors, {
        'dispatcher': 'subdomain',
        'response': builder.on_accept(),
    }),
)
