from flaskel.ext import default, limit
from flaskel.ext.auth import token_auth
from flaskel.ext.mongo import FlaskMongoDB
from flaskel.ext.redis import FlaskRedis
from flaskel.extra.mobile_support import MobileVersionCompatibility, RedisStore
from flaskel.extra.payments.stripe import PaymentHandler

from .auth import account_handler
from .database import database

ipban = limit.FlaskIPBan()
client_redis = FlaskRedis()
client_mongo = FlaskMongoDB()
scheduler = default.Scheduler()
payment_handler = PaymentHandler()
mobile_version = MobileVersionCompatibility()


class OPTS:
    cors = dict(
        resources={r"/*": {"origins": "*"}},
    )
    mobile_version = dict(
        store=RedisStore(client_redis),
    )
    errors = dict(
        dispatcher="subdomain",
        response=default.builder.on_accept(strict=False),
    )


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
    "token_auth": (token_auth,),
    "limiter": (limit.limiter,),
    "mobile_version": (mobile_version, OPTS.mobile_version),
    "mongo": (client_mongo,),
    "redis": (client_redis,),
    "scheduler": (scheduler,),
    "sendmail": (default.client_mail,),
    "stripe": (payment_handler,),
    "template": (default.template,),
    "useragent": (default.useragent,),
    "account": (account_handler,),
}
