import flask
from jwt import InvalidTokenError

from flaskel import cap, httpcode, webargs
from flaskel.ext import auth, builder
from . import bp_auth


@bp_auth.route('/token/access', methods=['POST'])
@webargs.query({
    'expire_access':  webargs.Fields.positive(missing=None),
    'expire_refresh': webargs.Fields.positive(missing=None),
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


@bp_auth.route('/token/revoke', methods=['POST'])
@builder.no_content
def revoke_tokens():
    try:
        if flask.request.json.access_token:
            auth.TokenHandler.revoke(flask.request.json.access_token)
        if flask.request.json.refresh_token:
            auth.TokenHandler.revoke(flask.request.json.refresh_token)
    except InvalidTokenError as exc:
        cap.logger.exception(exc)
        flask.abort(httpcode.UNPROCESSABLE_ENTITY, response="invalid token")
