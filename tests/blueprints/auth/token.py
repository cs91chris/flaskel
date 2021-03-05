import flask
from webargs import fields

from flaskel import httpcode
from flaskel.ext import auth
from flaskel import webargs
from . import bp_auth


@bp_auth.route('/token/access', methods=['POST'])
@webargs.query({
    'expire_access':  fields.Integer(missing=None, validate=lambda x: x > 0),
    'expire_refresh': fields.Integer(missing=None, validate=lambda x: x > 0),
})
def access_token(args):
    data = flask.request.json
    if data.email == 'email' and data.password == 'password':
        return auth.TokenHandler.create(
            data.email,
            expires_access=args['expire_access'],
            expires_refresh=args['expire_refresh']
        )

    flask.abort(httpcode.UNAUTHORIZED)


@bp_auth.route('/token/refresh', methods=['POST'])
@auth.jwt.jwt_refresh_token_required
def refresh_token():
    return auth.TokenHandler.refresh()


@bp_auth.route('/token/check', methods=['GET'])
@auth.jwt.jwt_required
def check_token():
    return auth.TokenHandler.dump()
