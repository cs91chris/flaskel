from .default import (
    builder,
    cfremote,
    cors,
    errors,
    logger,
    template
)
from .limit import FlaskIPBan, ip_ban, IPBan, limiter, RateLimit

# { "name": (extension, parameters: dict), }
BASE_EXTENSIONS = {
    "cfremote": (cfremote,),  # MUST be the first
    "logger":   (logger,),  # MUST be the second
    "template": (template,),
    "builder":  (builder,),
    "errors":   (errors, {
        "dispatcher": 'subdomain',
        "response":   builder.on_accept(strict=False),
    }),
}
