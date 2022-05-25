# Flaskel

Flaskel is a skeleton for all type of Flask application with rest apis or not.

## Features

- Application skeleton:
```shell
    flaskel init --help
```

- advanced app factory, see: ``flaskel.builder.AppBuilder``
- support for testing with ``flaskel.tester`` package
- collection of internal ext and external ext well integrated
- collection of custom flask views
- support multiple wsgi server, but gunicorn is well supported
- run app via cli with many options
- better configuration via multiple source: module, yaml (or json), env variables
- better http support for client and server, see: ``flaskel.http``

## Extensions

Extensions are registered via AppBuilder, see: ``flaskel.scripts.skeleton.ext``

Third parties extensions:

- Flask-APScheduler
- Flask-Caching
- Flask-Cors
- Flask-HTTPAuth
- Flask-JWT
- Flask-Limiter
- Flask-Mail
- Flask-SQLAlchemy
- Flask-PyMongo

My own external extensions:

- Flask-CloudflareRemote (cloudflareRemote)
- Flask-ErrorsHandler (errors_handler)
- Flask-Logify (logify)
- Flask-ResponseBuilder (response_builder)
- Flask-TemplateSupport (template_support)

Internal extensions:

- ``flaskel.ext.crypto.argon.Argon2`` (argon2)
- ``flaskel.ext.datetime.FlaskDateHelper`` (date_helper)
- ``flaskel.ext.limit.FlaskIPBan`` (ipban)
- ``flaskel.ext.redis.FlaskRedis`` (redis)
- ``flaskel.ext.useragent.UserAgent`` (useragent)
- ``flaskel.ext.redis.FlaskRedis`` (redis)
- ``flaskel.ext.sendmail.ClientMail`` (client_mail) extends Flask-Mail
- ``flaskel.ext.jobs.APJobs`` (scheduler) extends Flask-APScheduler
- ``flaskel.ext.mongo.FlaskMongoDB`` (mongo) extends Flask-PyMongo
- ``flaskel.ext.healthcheck.health.HealthCheck`` (healthcheck), default checks: glances, mongo, redis, sqlalchemy, system, services (http api)

Wrapper extensions:

- ``flaskel.ext.caching.Cache`` wraps Flask-Caching
- ``flaskel.ext.limit.RateLimit`` wraps Flask-Limiter
- ``flaskel.ext.auth.DBTokenHandler``, flaskel.ext.auth.RedisTokenHandler wraps Flask-JWT

Extra extensions:

- ``flaskel.extra.mobile_support.MobileVersionCompatibility`` (mobile_version)
- ``flaskel.extra.stripe.PaymentHandler`` (stripe)


## Views

Flaskel comes with useful views for most common apis or simple web controllers:

- ``flaskel.views.base.BaseView``
- ``flaskel.views.rpc.JSONRPCView``
- ``flaskel.views.template.RenderTemplate``
- ``flaskel.views.template.RenderTemplateString``
- ``flaskel.views.base.Resource``
- ``flaskel.views.resource.CatalogResource``
- ``flaskel.views.resource.Restful``
- ``flaskel.views.resource.PatchApiView``
- ``flaskel.views.proxy.ProxyView``
- ``flaskel.views.proxy.ConfProxyView``
- ``flaskel.views.proxy.TransparentProxyView``
- ``flaskel.views.proxy.JsonRPCProxy``
- ``flaskel.views.proxy.SchemaProxyView``
- ``flaskel.views.static.StaticFileView``
- ``flaskel.views.static.SPAView``
- ``flaskel.views.token.BaseTokenAuth``


Extra views:

- ``flaskel.extra.apidoc.ApiDocTemplate``
- ``flaskel.extra.apidoc.ApiSpecTemplate``
- ``flaskel.extra.media.ApiMedia``
- ``flaskel.extra.media.GetMedia``
- ``flaskel.extra.mobile_support.MobileReleaseView``


## SQLAlchemy support

Flaskel comes with auxiliaries components from sqlalchemy:

- dump schema via cli:

```shell
    flaskel schema --help
```

- custom Model class than adds functionalities to all models

```python
class SQLAModel(Model):
    def columns(self): ...
    def get_one(cls, raise_not_found=True, to_dict=True, *args, **kwargs): ...
    def get_list(cls, to_dict=True, restricted=False, order_by=None, page=None, page_size=None, max_per_page=None, *args, **kwargs): ...
    def query_collection(cls, params=None, *args, **kwargs): ...
    def update(self, attributes): ...
```

- models mixins, for common use cases

```python
class StandardMixin: ...
class CatalogMixin: ...
class CatalogXMixin(CatalogMixin): ...
class LoaderMixin: ...
class UserMixin(StandardMixin): ...
class DictableMixin:
    def to_dict(self, restricted=False): ...
```

- Support class for common problems

```python
class SQLASupport:
    def __init__(self, model, session): ...

    def get_or_create(self, defaults=None, **kwargs):
        """
        :param defaults: attribute used to create record
        :param kwargs: filters used to fetch record or create
        :return: obj, created (bool)
        """

    def update_or_create(self, defaults=None, **kwargs):
        """
        :param defaults: attribute used to create record
        :param kwargs: filters used to fetch record or create
        :return: obj, created (bool)
        """
    @staticmethod
    def exec_from_file(db_uri, filename, echo=False):
        """
        :param db_uri: database url connection
        :param filename: sql file name
        :param echo: enable sqlalchemy echo
        """
```


## Data Structures

```python
class ConfigProxy: ...
class ExtProxy: ...
class HashableDict(dict): ...
class ObjectDict(dict): ...

class IntEnum(enum.IntEnum):
    @classmethod
    def to_list(cls): ...
    def to_dict(self): ...

class Dumper:
    def __init__(self, data, callback=None, *args, **kwargs): ...
    def dump(self): ...
```


## Webargs support

```python
from flaskel import webargs

@webargs.query(...)
...

@webargs.payload(...)
...

@webargs.query_paginate()
...

webargs.paginate()

webargs.Field.integer()
webargs.Field.string()
webargs.Field.decimal()
webargs.Field.boolean()
webargs.Field.positive()
webargs.Field.not_negative()
webargs.Field.not_positive()
webargs.Field.negative()
webargs.Field.isodate()
webargs.Field.list_of()

webargs.OptField.integer()
webargs.OptField.string()
webargs.OptField.decimal()
webargs.OptField.boolean()
webargs.OptField.positive()
webargs.OptField.not_negative()
webargs.OptField.not_positive()
webargs.OptField.negative()
webargs.OptField.isodate()
webargs.OptField.list_of()

webargs.ReqField.integer()
webargs.ReqField.string()
webargs.ReqField.decimal()
webargs.ReqField.boolean()
webargs.ReqField.positive()
webargs.ReqField.not_negative()
webargs.ReqField.not_positive()
webargs.ReqField.negative()
webargs.ReqField.isodate()
webargs.ReqField.list_of()
```


## JSON schema support

```python
class JSONSchema:
    @classmethod
    def load_from_url(cls, url): ...

    @classmethod
    def load_from_file(cls, file): ...

    @classmethod
    def validate(cls, data, schema, raise_exc=False, pretty_error=True, checker=None): ...
```

```python
class PayloadValidator:
    schemas = SCHEMAS
    validator = JSONSchema

    @classmethod
    def validate(cls, schema, strict=True): ...
```

```python
Fields.schema
Fields.null
Fields.integer
Fields.string
Fields.number
Fields.boolean
Fields.datetime
Fields.any_object
Fields.any
Fields.Opt.integer
Fields.Opt.string
Fields.Opt.number
Fields.Opt.boolean

class Fields:
    @classmethod
    def oneof(cls, *args, **kwargs): ...

    @classmethod
    def anyof(cls, *args, **kwargs): ...

    @classmethod
    def ref(cls, path, **kwargs): ...

    @classmethod
    def enum(cls, *args, **kwargs): ...

    @classmethod
    def type(cls, *args, **kwargs): ...

    @classmethod
    def object(cls, required=(), not_required=(), properties=None, all_required=True, additional=False, **kwargs): ...

    @classmethod
    def array(cls, items, min_items=0, **kwargs): ...

    @classmethod
    def array_object(cls, min_items=0, **kwargs): ...
```


## Configuration

There are many configuration keys provided by many sources, the same key in different source are overridden.
Source priorities (low to high):

- python module: all defaults [flaskel.config](flaskel/config.py)
- mapping (dict): via cli from yaml or json file
- python module: via environment variable ``APP_CONFIG_FILE``
- environment variables: handled via ``python-decouple``, so can be stored in .env or settings.ini file

Configuration via env:

- ``DEBUG``: *(default: bool = True)*
- ``TESTING``: *(default: bool = DEBUG)*
- ``APP_NAME``: *(default = flaskel)*
- ``APP_HOST``: *(default = 127.0.0.1)*
- ``APP_PORT``: *(default: int = 5000)*
- ``FLASK_APP``: *(default = app:app)*
- ``SERVER_NAME``: *(default = APP_HOST:APP_PORT)*
- ``FLASK_ENV``: *(default = development)*
- ``LOCALE``: *(default = "en_EN.utf8")*
- ``JWT_ALGORITHM``: *(default = "HS512")*
- ``JWT_ACCESS_TOKEN_EXPIRES``: *(default: 1 day)*
- ``JWT_REFRESH_TOKEN_EXPIRES``: *(default: 14 day)*
- ``TEMPLATES_AUTO_RELOAD``: *(default: bool = DEBUG)*
- ``EXPLAIN_TEMPLATE_LOADING``: *(default: bool = False)*
- ``SEND_FILE_MAX_AGE_DEFAULT``: *(default: 1 day)*
- ``APIDOCS_ENABLED``: *(default: bool = True)*
- ``CONF_PATH``: *(default = flaskel/scripts/skeleton/res)*
- ``SQLALCHEMY_DATABASE_URI``: *(default = sqlite:///db.sqlite)*
- ``REDIS_URL``: *(default = mongodb://localhost)*
- ``REDIS_CONN_TIMEOUT``: *(default: float = 0.05)*
- ``MONGO_URI``: *(default = redis://127.0.0.1:6379)*
- ``MONGO_CONN_TIMEOUT_MS``: *(default: int = 100)*
- ``MONGO_SERVER_SELECTION_TIMEOUT_MS``: *(default: int = 100)*
- ``BASIC_AUTH_USERNAME``: *(default = admin)*
- ``BASIC_AUTH_PASSWORD``: *(default = admin)*
- ``ADMIN_EMAIL``: *(default = admin)*
- ``ADMIN_PASSWORD``: *(default = admin)*
- ``MAIL_DEBUG``: *(default: bool = DEBUG)*
- ``MAIL_SERVER``: *(default = sendria.local)*
- ``MAIL_PORT``: *(default: int = 62000)*
- ``MAIL_USERNAME``: *(default: "")*
- ``MAIL_PASSWORD``: *(default: "")*
- ``MAIL_USE_SSL``: *(default: bool = False)*
- ``MAIL_USE_TLS``: *(default: bool = False)*
- ``MAIL_DEFAULT_SENDER``: *(default = admin@mail.com)*
- ``MAIL_DEFAULT_RECEIVER``: *(default = admin@mail.com)*
- ``MAIL_RECIPIENT``: *(default: admin@mail.com)*
- ``MAIL_TIMEOUT``: *(default: int = 60)*
- ``PREFERRED_URL_SCHEME``: *(default = http if FLASK_ENV = development else https)*
- ``LOG_BUILDER``: *(default = text)*
- ``LOG_APP_NAME``: *(default = APP_NAME)*
- ``LOG_LOGGER_NAME``: *(default = FLASK_ENV)*
- ``LOG_REQ_SKIP_DUMP``: *(default = not TESTING)*
- ``LOG_RESP_SKIP_DUMP``: *(default = not TESTING)*
- ``LOG_RESP_HEADERS``: *(default = [])*
- ``LOG_REQ_HEADERS``: *(default = [])*
- ``CF_STRICT_ACCESS``: *(default = False)*
- ``VERSION_STORE_MAX``: *(default = 6)*
- ``VERSION_CACHE_EXPIRE``: *(default = 60)*
- ``HTTP_PROTECT_BODY``: *(default = False)*
- ``HTTP_DUMP_REQ_BODY``: *(default = False)*
- ``HTTP_DUMP_RESP_BODY``: *(default = False)*
- ``HTTP_SSL_VERIFY``: *(default = True)*
- ``HTTP_TIMEOUT``: *(default = 10)*
- ``USE_X_SENDFILE``: *(default = not DEBUG)*
- ``ENABLE_ACCEL``: *(default = True)*
- ``WSGI_WERKZEUG_LINT_ENABLED``: *(default = TESTING)*
- ``WSGI_WERKZEUG_PROFILER_ENABLED``: *(default = TESTING)*
- ``WSGI_WERKZEUG_PROFILER_FILE``: *(default = "profiler.txt")*
- ``WSGI_WERKZEUG_PROFILER_RESTRICTION``: *(default: list = [0.1])
- ``SQLALCHEMY_ECHO``: *(default = TESTING)*
- ``JSONRPC_BATCH_MAX_REQUEST``: *(default = 10)*
- ``IPBAN_ENABLED``: *(default = True)*
- ``IPBAN_KEY_PREFIX``: *(default = APP_NAME)*
- ``IPBAN_KEY_SEP``: *(default = /)*
- ``IPBAN_BACKEND``: *(default = local)*
- ``IPBAN_BACKEND_OPTS``: *(default = {})*
- ``IPBAN_COUNT``: *(default = 5)*
- ``IPBAN_SECONDS``: *(default = 3600)*
- ``IPBAN_NET_WHITELIST``: *(default = 127.0.0.0/8)*
- ``IPBAN_IP_WHITELIST``: *(default = 127.0.0.1)*
- ``IPBAN_STATUS_CODE``: *(default = 403)*
- ``IPBAN_CHECK_CODES``: *(default = 404,405,501)*
- ``RATELIMIT_ENABLED``: *(default = not DEBUG)*
- ``RATELIMIT_HEADERS_ENABLED``: *(default = True)*
- ``RATELIMIT_IN_MEMORY_FALLBACK_ENABLED``: *(default = True)*
- ``RATELIMIT_STORAGE_URL``: *(default = REDIS_URL)*
- ``RATELIMIT_KEY_PREFIX``: *(default = APP_NAME)*
- ``SCHEDULER_AUTO_START``: *(default = True)*
- ``SCHEDULER_API_ENABLED``: *(default = False)*
- ``CACHE_KEY_PREFIX``: *(default = APP_NAME)*
- ``CACHE_REDIS_URL``: *(default = REDIS_URL)*
- ``CACHE_DEFAULT_TIMEOUT``: *(default = 1 hour)*
- ``CACHE_DISABLED``: *(default = False)*

Static application configuration:

- ``ERROR_PAGE``: *(default = "core/error.html")*
- ``DATABASE_URL``: *(default = SQLALCHEMY_DATABASE_URI)*
- ``SECRET_KEY_MIN_LENGTH``: *(default: int = 256)*
- ``PRETTY_DATE``: *(default = "%d %B %Y %I:%M %p")*
- ``DATE_ISO_FORMAT``: *(default = "%Y-%m-%dT%H:%M:%S")*
- ``JWT_DEFAULT_SCOPE``: *(default = None)*
- ``JWT_DEFAULT_TOKEN_TYPE``: *(default = "bearer")*
- ``JWT_TOKEN_LOCATION``: *(default = ["headers", "query_string"])*
- ``HTTP_DUMP_BODY``: *(default: [False, False])*
- ``ACCEL_BUFFERING``: *(default = True)*
- ``ACCEL_CHARSET``: *(default = "utf-8")*
- ``ACCEL_LIMIT_RATE``: *(default = "off")*
- ``RB_DEFAULT_ACCEPTABLE_MIMETYPES``: *(default = ["application/json", "application/xml"])*
- ``REQUEST_ID_HEADER``: *(default = "X-Request-ID")*
- ``CACHE_TYPE``: *(default = "flask_caching.backends.redis")*
- ``CACHE_OPTIONS``: *(dict)*
- ``CORS_EXPOSE_HEADERS``: *(list)*
- ``RATELIMIT_STORAGE_OPTIONS``: *(dict)*
- ``SCHEDULER_JOBSTORES``: *(dict)*
- ``SCHEDULER_EXECUTORS``: *(dict)*
- ``SCHEDULER_JOB_DEFAULTS``: *(dict)*
- ``LIMITER``: *(dict)*
   - ``FAIL``: *(default = "1/second")*
   - ``FAST``: *(default = "30/minute")*
   - ``MEDIUM``: *(default = "20/minute")*
   - ``SLOW``: *(default = "10/minute")*
   - ``BYPASS_KEY``: *(default = "X-Limiter-Bypass")*
   - ``BYPASS_VALUE``: *(default = "bypass-rate-limit")*


Extra configurations are optionally loaded via files in folder ``CONF_PATH``:

- ``APISPEC``: *(swagger.yaml)*
- ``SCHEMAS``: *(schemas.yaml)*
- ``SCHEDULER_JOBS``: *(scheduler.yaml)*
- ``IPBAN_NUISANCES``: *(nuisances.yaml)*
- ``LOGGING``: *(log.yaml)* if missing, default ``flaskel.utils.logger:LOGGING`` is used


Configuration specific for internal extensions:


- flaskel.ext.crypto.argon.Argon2
- ``ARGON2_ENCODING``: *(default = utf-8)*
- ``ARGON2_TIME_COST``: *(default = 3)*
- ``ARGON2_HASH_LEN``: *(default = 32)*
- ``ARGON2_PARALLELISM``: *(default = 4)*
- ``ARGON2_SALT_LEN``: *(default = 16)*
- ``ARGON2_MEMORY_COST``: *(default = 65536)* 64 MiB
- ``ARGON2_PROFILE``: *(default = low)* allowed low|high


- flaskel.ext.healthcheck.health.HealthCheck
 - ``HEALTHCHECK_ABOUT_LINK``: *(default = None)*
 - ``HEALTHCHECK_VIEW_NAME``: *(default = healthcheck)*
 - ``HEALTHCHECK_PATH``: *(default = /healthcheck)*
 - ``HEALTHCHECK_PARAM_KEY``: *(default = checks)*
 - ``HEALTHCHECK_PARAM_SEP``: *(default = +)*
 - ``HEALTHCHECK_CONTENT_TYPE``: *(default = application/health+json)*


- flaskel.ext.datetime.FlaskDateHelper
 - ``DATE_HELPER_COUNTRY``: *(default = IT)*
 - ``DATE_HELPER_PROV``: *(default = None)*
 - ``DATE_HELPER_STATE``: *(default = None)*
 - ``DATE_ISO_FORMAT``: *(default = "%Y-%m-%dT%H:%M:%S")*
 - ``DATE_PRETTY``: *(default = "%d %B %Y %I:%M %p")*


- flaskel.ext.jobs.APJobs
 - ``SCHEDULER_AUTO_START``: *(default = False)*
 - ``SCHEDULER_PATCH_MULTITHREAD``: *(default = True)*
 - ``SCHEDULER_LOCK_FILE``: *(default = .scheduler.lock)*


- flaskel.ext.ipban.FlaskIPBan
 - ``IPBAN_ENABLED``: *(default = True)*
 - ``IPBAN_KEY_PREFIX``: *(default = APP_NAME)*
 - ``IPBAN_KEY_SEP``: *(default = /)*
 - ``IPBAN_BACKEND``: *(default = local)*
 - ``IPBAN_BACKEND_OPTS``: *(default = {})*
 - ``IPBAN_COUNT``: *(default = 5)*
 - ``IPBAN_SECONDS``: *(default = 3600)*
 - ``IPBAN_NET_WHITELIST``: *(default = 127.0.0.0/8)*
 - ``IPBAN_IP_WHITELIST``: *(default = 127.0.0.1)*
 - ``IPBAN_STATUS_CODE``: *(default = 403)*
 - ``IPBAN_CHECK_CODES``: *(default = 404,405,501)*

- flaskel.ext.caching.Caching
 - ``CACHE_TYPE``: *(default = "flask_caching.backends.redis")*
 - ``CACHE_REDIS_URL``: *(default = REDIS_URL)*
 - ``CACHE_DEFAULT_TIMEOUT``: *(default = Seconds.hour)*
 - ``CACHE_KEY_PREFIX``: *(default = APP_NAME)*
 - ``CACHE_OPTIONS``: *(dict)* passed to redis client instance


- flaskel.ext.redis.FlaskRedis
 - ``REDIS_URL``: *(default = redis://localhost:6379/0)*
 - ``REDIS_OPTS``: *(dict)* passed to redis client instance


- flaskel.ext.mongo.FlaskMongoDB
 - ``MONGO_URI``: *(default = mongodb://localhost)*
 - ``MONGO_OPTS``: *(dict)* passed to mongodb client instance


- flaskel.ext.useragent.UserAgent
 - ``USER_AGENT_AUTO_PARSE``: *(default = False)*


- flaskel.extra.stripe.PaymentHandler (stripe)
 - ``STRIPE_SECRET_KEY``:
 - ``STRIPE_PUBLIC_KEY``:
 - ``STRIPE_WEBHOOK_SECRET``:
 - ``STRIPE_DEBUG``: *(default = False)*
 - ``STRIPE_DEFAULT_CURRENCY``: *(default = eur)*
 - ``STRIPE_API_VERSION``: *(default = 2020-08-27)*


- flaskel.extra.mobile_support.MobileVersionCompatibility (mobile_version)
 - ``VERSION_STORE_MAX``: *(default = 6)*
 - ``VERSION_CACHE_EXPIRE``: *(default = 3600)*
 - ``VERSION_CHECK_ENABLED``: *(default = True)*
 - ``VERSION_AGENT_HEADER``: *(default = X-Agent)*
 - ``VERSION_API_HEADER``: *(default = X-Api-Version)*
 - ``VERSION_STORE_KEY``: *(default = x_upgrade_needed)*
 - ``VERSION_HEADER_KEY``: *(default = X-Mobile-Version)*
 - ``VERSION_UPGRADE_HEADER``: *(default = X-Upgrade-Needed)*
 - ``VERSION_AGENTS``: *(default = (android, ios))*
 - ``VERSION_SKIP_STATUSES``: *(default = (FORBIDDEN, NOT_FOUND, METHOD_NOT_ALLOWED, TOO_MANY_REQUESTS))*


- flaskel.extra.notification.NotificationHandler
 - ``FCM_API_KEY``: mandatory if used


- flaskel.extra.media.service.MediaService
- ``MEDIA``: *(dict)*
  - ``ALLOWED_EXTENSIONS``: *(default: [png,jpg])*
  - ``UPLOAD_FOLDER``:
  - ``EXTERNAL_URL``:

