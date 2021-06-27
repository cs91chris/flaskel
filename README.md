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
- ``flaskel.ext.sendmail.ClientMail`` (client_mail) extends Flask-Mail
- ``flaskel.ext.jobs.APJobs`` (scheduler) extends Flask-APScheduler
- ``flaskel.ext.healthcheck.health.HealthCheck`` (healthcheck), default checks: glances, mongo, redis, sqlalchemy, system

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
- ``flaskel.views.proxy.ProxyView``
- ``flaskel.views.proxy.ConfProxyView``
- ``flaskel.views.proxy.TransparentProxyView``

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
    def to_dict(self, restricted=False): ...
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

## Configuration

There are many configuration keys provided by many sources, the same key in different source are overridden.
Source priorities:

- python module: default ``flaskel.config``
- mapping (dict): via cli from yaml or json file
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
- ``TEMPLATES_AUTO_RELOAD``: *(default: bool = DEBUG)*
- ``EXPLAIN_TEMPLATE_LOADING``: *(default: bool = False)*
- ``APIDOCS_ENABLED``: *(default: bool = True)*
- ``CONF_PATH``: *(default = flaskel/scripts/skeleton/res)*
- ``SQLALCHEMY_DATABASE_URI``: *(default = sqlite:///db.sqlite)*
- ``REDIS_URL``: *(default = redis://127.0.0.1:6379)*
- ``REDIS_CONN_TIMEOUT``: *(default: float = 0.05)*
- ``BASIC_AUTH_USERNAME``: *(default = admin)*
- ``BASIC_AUTH_PASSWORD``: *(default = admin)*
- ``MAIL_DEBUG``: *(default: bool = DEBUG)*
- ``MAIL_SERVER``: *(default = sendria.local)*
- ``MAIL_PORT``: *(default: int = 62000)*
- ``ADMIN_EMAIL``: *(default = admin)*
- ``ADMIN_PASSWORD``: *(default = admin)*
- ``MAIL_DEFAULT_SENDER``: *(default = admin@mail.com)*
- ``MAIL_DEFAULT_RECEIVER``: *(default = admin@mail.com)*
- ``PREFERRED_URL_SCHEME``: *(default = http if FLASK_ENV = development else https)*
- ``IPBAN_COUNT``: *(default = 5)*
- ``IPBAN_SECONDS``: *(default = 3600)*
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
- ``USE_X_SENDFILE``: *(default = not DEBUG)*
- ``ENABLE_ACCEL``: *(default = True)*
- ``WSGI_WERKZEUG_LINT_ENABLED``: *(default = TESTING)*
- ``WSGI_WERKZEUG_PROFILER_ENABLED``: *(default = TESTING)*
- ``SQLALCHEMY_ECHO``: *(default = TESTING)*
- ``RATELIMIT_ENABLED``: *(default = not DEBUG)*
- ``RATELIMIT_HEADERS_ENABLED``: *(default = True)*
- ``RATELIMIT_IN_MEMORY_FALLBACK_ENABLED``: *(default = True)*
- ``SCHEDULER_AUTO_START``: *(default = True)*
- ``SCHEDULER_API_ENABLED``: *(default = False)*
- ``CACHE_KEY_PREFIX``: *(default = APP_NAME)*

Extra configurations are optionally loaded via files in folder ``CONF_PATH``:

- ``APISPEC``: *(swagger.yaml)*
- ``SCHEMAS``: *(schemas.yaml)*
- ``SCHEDULER_JOBS``: *(scheduler.yaml)*
- ``IPBAN_NUISANCES``: *(nuisances.yaml)*
- ``LOGGING``: *(log.yaml)* if missing, default ``flaskel.utils.logger:LOGGING`` is used


Configuration specific for internal extensions:

- flaskel.ext.crypto.argon.Argon2
 - ``ARGON2_ENCODING``
 - ``ARGON2_TIME_COST``
 - ``ARGON2_HASH_LEN``
 - ``ARGON2_MEMORY_COST``
 - ``ARGON2_PARALLELISM``
 - ``ARGON2_SALT_LEN``

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
 - ``SCHEDULER_PATCH_MULTIPROCESS``: *(default = True)*
 - ``SCHEDULER_LOCK_FILE``: *(default = .scheduler.lock)*

- flaskel.ext.limit.FlaskIPBan
 - ``IPBAN_ENABLED``: *(default = True)*
 - ``IPBAN_COUNT``: *(default = 20)*
 - ``IPBAN_SECONDS``: *(default = Day.seconds)*
 - ``IPBAN_NUISANCES``: *(default = nuisances)*
 - ``IPBAN_STATUS_CODE``: *(default = FORBIDDEN)*
 - ``IPBAN_CHECK_CODES``: *(default = (NOT_FOUND, METHOD_NOT_ALLOWED, NOT_IMPLEMENTED))*

- flaskel.ext.redis.FlaskRedis
 - ``REDIS_URL``: *(default = redis://localhost:6379/0)*
 - ``REDIS_OPTS``: passed to redis client instance

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
