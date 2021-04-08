from flaskel.ext import caching, client_mail, client_redis, default, errors, limit, scheduler, useragent
from flaskel.ext.auth import jwtm
from flaskel.ext.crypto import argon2
from flaskel.ext.healthcheck import health_checks
from flaskel.ext.sqlalchemy import db as sqlalchemy

EXTENSIONS = {
    # "name":   (<extension>, parameters: dict)
    "cfremote":      (default.cfremote,),  # MUST be the first
    "logger":        (default.logger,),  # MUST be the second
    "template":      (default.template,),
    "builder":       (default.builder,),
    "cors":          (default.cors, {
        "resources": {
            r'/*': {'origins': '*'}
        }
    }),
    "database":      (sqlalchemy,),
    "limiter":       (limit.limiter,),
    "ip_ban":        (limit.ip_ban,),
    "cache":         (caching,),
    "errors":        (errors.error_handler, {
        "dispatcher": 'subdomain',
        "response":   default.builder.on_accept(strict=False),
        "normalizer": errors.ErrorNormalizer()
    }),
    "useragent":     (useragent,),
    "argon2":        (argon2,),
    "caching":       (caching,),
    "scheduler":     (scheduler,),
    "sendmail":      (client_mail,),
    "redis":         (client_redis,),
    "health_checks": (health_checks,),
    "jwt":           (jwtm,),
    "ipban":         (limit.ip_ban,),
}
