from flaskel import ExtProxy
from flaskel.ext import auth
from flaskel.views.token import BaseTokenAuth


class TokenAuthView(BaseTokenAuth):
    handler = auth.RedisTokenHandler(ExtProxy("redis"))
