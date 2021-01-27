from .checks import health_glances, health_mongo, health_redis, health_sqlalchemy, health_system
from .health import HealthCheck

health_checks = HealthCheck()
