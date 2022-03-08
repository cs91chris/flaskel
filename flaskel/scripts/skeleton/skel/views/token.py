from flaskel import client_redis
from flaskel.ext import auth
from flaskel.views.token import BaseTokenAuth


class TokenAuthView(BaseTokenAuth):
    handler = auth.RedisTokenHandler(client_redis)
