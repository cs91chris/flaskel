from flaskel.ext import (
    caching,
    client_mail,
    client_redis,
    date_helper,
    default,
    errors,
    limit,
    scheduler,
    useragent,
)
from flaskel.ext.auth import jwtm
from flaskel.ext.crypto import argon2
from flaskel.ext.healthcheck import health_checks
from flaskel.ext.sqlalchemy import db as sqlalchemy
from flaskel.extra.mobile_support import mobile_version, RedisStore
from flaskel.extra.stripe import payment_handler


class OPTS:
    cors = dict(resources={r"/*": {"origins": "*"}})
    mobile_version = dict(store=RedisStore(client_redis))
    errors = dict(
        dispatcher="subdomain",
        response=default.builder.on_accept(strict=False),
    )


EXTENSIONS = {
    # "name":   (<extension>, parameters: dict)
    "cfremote": (default.cfremote,),  # MUST be the first
    "logger": (default.logger,),  # MUST be the second
    "template": (default.template,),
    "builder": (default.builder,),
    "date_helper": (date_helper,),
    "cors": (default.cors, OPTS.cors),
    "database": (sqlalchemy,),
    "limiter": (limit.limiter,),
    "ip_ban": (limit.ip_ban,),
    "cache": (caching,),
    "errors": (errors.error_handler, OPTS.errors),
    "useragent": (useragent,),
    "argon2": (argon2,),
    "caching": (caching,),
    "scheduler": (scheduler,),
    "sendmail": (client_mail,),
    "redis": (client_redis,),
    "health_checks": (health_checks,),
    "jwt": (jwtm,),
    "ipban": (limit.ip_ban,),
    "stripe": (payment_handler,),
    "mobile_version": (mobile_version, OPTS.mobile_version),
}
