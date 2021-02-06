import flask
from jwt import InvalidTokenError
from webargs import fields

from flaskel import cap, httpcode
from flaskel.ext import builder
from flaskel.ext.auth import jwt, TokenHandler
from flaskel.utils.webargs import query
from . import auth


@auth.route('/token/access', methods=['POST'])
@query({
    'expire_access':  fields.Integer(missing=None, validate=lambda x: x > 0),
    'expire_refresh': fields.Integer(missing=None, validate=lambda x: x > 0),
})
def access_token(args):
    data = flask.request.json
    if data.email == 'email' and data.password == 'password':
        return TokenHandler.create(
            data.email,
            expires_access=args['expire_access'],
            expires_refresh=args['expire_refresh']
        )

    flask.abort(httpcode.UNAUTHORIZED)


@auth.route('/token/refresh', methods=['POST'])
@jwt.jwt_refresh_token_required
def refresh_token():
    return TokenHandler.refresh()


@auth.route('/token/check', methods=['GET'])
@jwt.jwt_required
def check_token():
    return TokenHandler.dump()


@auth.route('/token/revoke', methods=['POST'])
@builder.no_content
def revoke_tokens():
    try:
        if flask.request.json.access_token:
            TokenHandler.revoke(flask.request.json.access_token)
        if flask.request.json.refresh_token:
            TokenHandler.revoke(flask.request.json.refresh_token)
    except InvalidTokenError as exc:
        cap.logger.exception(exc)
        flask.abort(httpcode.UNPROCESSABLE_ENTITY, response="invalid token")
