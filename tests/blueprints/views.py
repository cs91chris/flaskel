from flaskel import ConfigProxy
from flaskel.ext import auth
from flaskel.ext.auth import basic_auth
from flaskel.ext.sqlalchemy import db
from flaskel.views.resource import Restful
from flaskel.views.token import BaseTokenAuth


class BlackListToken(db.Model, auth.RevokedTokenMixin):
    __tablename__ = "revoked_tokens"


class TokenAuthView(BaseTokenAuth):
    handler = auth.DBTokenHandler(BlackListToken, db.session)


class ApiItem(Restful):
    post_schema = ConfigProxy("SCHEMAS.ITEM_POST")
    decorators = [basic_auth.login_required]
