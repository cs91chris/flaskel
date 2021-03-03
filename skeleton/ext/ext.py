from flaskel.ext import default, limit
from flaskel.ext.auth import jwtm
from flaskel.ext.caching import caching
from flaskel.ext.crypto.argon import argon2
from flaskel.ext.healthcheck.health import health_checks
from flaskel.ext.jobs import scheduler
from flaskel.ext.redis import client_redis
from flaskel.ext.sendmail import client_mail
from flaskel.ext.sqlalchemy.ext import db as sqlalchemy
from flaskel.ext.useragent import useragent

EXTENSIONS = {
    # "name":   (<extension>, parameters: dict)
    "cfremote":      (default.cfremote,),  # MUST be the first
    "logger":        (default.logger,),  # MUST be the second
    "template":      (default.template,),
    "builder":       (default.builder,),
    "cors":          (default.cors,),
    "database":      (sqlalchemy,),
    "limiter":       (limit.limiter,),
    "ip_ban":        (limit.ip_ban,),
    "cache":         (caching,),
    "errors":        (default.errors, {
        "dispatcher": 'subdomain',
        "response":   default.builder.on_accept(strict=False),
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
