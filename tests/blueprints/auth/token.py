import flask
from flask import current_app as cap
from webargs import fields

from flaskel import httpcode
from flaskel.ext.auth import basic_auth, create_tokens, jwt, refresh_access_token
from flaskel.utils.webargs import query
from . import auth


@auth.route('/access_token', methods=['POST'])
@basic_auth.login_required()
@query({
    'expire_access':  fields.Integer(missing=None, validate=lambda x: x > 0),
    'expire_refresh': fields.Integer(missing=None, validate=lambda x: x > 0),
})
def access_token(args):
    data = flask.request.json
    if data.email == 'email' and data.password == 'password':
        return create_tokens(
            data.email,
            expires_access=args['expire_access'],
            expires_refresh=args['expire_refresh'],
        )

    flask.abort(httpcode.UNAUTHORIZED)


@auth.route('/refresh_token', methods=['GET', 'POST'])
@jwt.jwt_refresh_token_required
def refresh_token():
    return refresh_access_token()


@auth.route('/check_token', methods=['GET'])
@jwt.jwt_required
def token_check():
    return dict(
        token_type=cap.config['JWT_DEFAULT_TOKEN_TYPE'],
        scope=cap.config['JWT_DEFAULT_SCOPE'],
        **jwt.get_raw_jwt()
    )
