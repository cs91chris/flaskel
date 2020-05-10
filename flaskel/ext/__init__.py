from .default import (
    argon2,
    builder,
    cfremote,
    cors,
    errors,
    logger,
    template
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
