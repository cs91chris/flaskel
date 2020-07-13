from .default import (
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
    (template,),
    (cfremote,),
    (builder,),
    (errors, {
        'dispatcher': 'subdomain',
        'response': builder.on_accept(),
    }),
)
