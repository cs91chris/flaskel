# Define your extensions in this package and import them here
from flaskel.ext import caching, cors, ip_ban, limit
from flaskel.ext.sqlalchemy import db

EXTENSIONS = {
    # "name":   (<extension>, parameters: dict)
    "cors":     (cors,),
    "database": (db,),
    "template": None,
    "limiter":  (limit.limiter,),
    "ip_ban":   (ip_ban,),
    "cache":    (caching,),
}
