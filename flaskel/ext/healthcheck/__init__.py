from .checks import health_mongo, health_redis, health_sqlalchemy
from .health import HealthCheck

health_checks = HealthCheck()
