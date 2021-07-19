import flask

from flaskel import httpcode, webargs
from flaskel.ext import auth, builder
from flaskel.ext.sqlalchemy import db
from . import bp_auth


class BlackListToken(db.Model, auth.RevokedTokenMixin):
    __tablename__ = "revoked_tokens"


handler = auth.DBTokenHandler(BlackListToken, db.session)


@bp_auth.route("/token/access", methods=["POST"])
@webargs.query(
    dict(
        expires_access=webargs.OptField.positive(),
        expires_refresh=webargs.OptField.positive(),
    )
)
def access_token(args):
    data = flask.request.json
    if data.email == "email" and data.password == "password":
        return handler.create(data.email, **args)
    flask.abort(httpcode.UNAUTHORIZED)


@bp_auth.route("/token/refresh", methods=["POST"])
@auth.jwt.jwt_required(refresh=True)
def refresh_token():
    return handler.refresh()


@bp_auth.route("/token/check", methods=["GET"])
@auth.jwt.jwt_required()
def check_token():
    return handler.dump()


@bp_auth.route("/token/revoke", methods=["POST"])
@builder.no_content
def revoke_token():
    data = flask.request.json
    if data.access_token:
        handler.revoke(data.access_token)
    if data.refresh_token:
        handler.revoke(data.refresh_token)
