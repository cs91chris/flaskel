from models.user import AccountModel
from vbcore.datastruct import ObjectDict

from flaskel import client_redis
from flaskel.ext import auth
from flaskel.extra.account import AccountHandler


class TokenHandler(auth.RedisTokenHandler):
    def prepare_identity(self, data, **__):
        return ObjectDict(id=data.id, email=data.email)


token_handler = TokenHandler(client_redis)
account_handler = AccountHandler(model=AccountModel)
