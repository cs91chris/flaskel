from .default import (
    builder,
    cfremote,
    cors,
    errors,
    logger,
    template
)

# { "name": (extension, parameters: dict), }
BASE_EXTENSIONS = {
    "logger":   (logger,),
    "template": (template,),
    "cfremote": (cfremote,),
    "builder":  (builder,),
    "errors":   (errors, {
        "dispatcher": 'subdomain',
        "response":   builder.on_accept(),
    }),
}
