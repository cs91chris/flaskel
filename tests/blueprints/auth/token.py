import flask

from flaskel import httpcode, webargs
from flaskel.ext import auth
from . import bp_auth


@bp_auth.route('/token/access', methods=['POST'])
@webargs.query(dict(
    expires_access=webargs.OptField.positive(),
    expires_refresh=webargs.OptField.positive()
))
def access_token(args):
    data = flask.request.json
    if data.email == 'email' and data.password == 'password':
        return auth.TokenHandler.create(data.email, **args)
    flask.abort(httpcode.UNAUTHORIZED)


@bp_auth.route('/token/refresh', methods=['POST'])
@auth.jwt.jwt_required(refresh=True)
def refresh_token():
    return auth.TokenHandler.refresh()


@bp_auth.route('/token/check', methods=['GET'])
@auth.jwt.jwt_required()
def check_token():
    return auth.TokenHandler.dump()
