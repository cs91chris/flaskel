from flaskel.ext import limit, default
from flaskel.extra.mobile_support import RedisStore, MobileVersionCompatibility
from flaskel.extra.stripe import PaymentHandler


class OPTS:
    cors = dict(
        resources={r"/*": {"origins": "*"}},
    )
    mobile_version = dict(
        store=RedisStore(default.client_redis),
    )
    errors = dict(
        dispatcher="subdomain",
        response=default.builder.on_accept(strict=False),
    )


ipban = limit.FlaskIPBan()
database = default.Database()
scheduler = default.Scheduler()
payment_handler = PaymentHandler()
mobile_version = MobileVersionCompatibility()

EXTENSIONS = {
    "cfremote": (default.cfremote,),  # MUST be the first
    "logger": (default.logger,),  # MUST be the second
    "argon2": (default.argon2,),
    "builder": (default.builder,),
    "cache": (default.caching,),
    "cors": (default.cors, OPTS.cors),
    "database": (database,),
    "date_helper": (default.date_helper,),
    "errors": (default.error_handler, OPTS.errors),
    "health_checks": (default.health_checks,),
    "ip_ban": (ipban,),
    "token_auth": (default.token_auth,),
    "limiter": (limit.limiter,),
    "mobile_version": (mobile_version, OPTS.mobile_version),
    "mongo": (default.client_mongo,),
    "redis": (default.client_redis,),
    "scheduler": (scheduler,),
    "sendmail": (default.client_mail,),
    "stripe": (payment_handler,),
    "template": (default.template,),
    "useragent": (default.useragent,),
}
