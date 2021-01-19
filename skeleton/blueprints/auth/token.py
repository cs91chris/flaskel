import flask
from flask import current_app as cap

from . import auth
from flaskel.ext.auth import jwt, create_tokens, refresh_access_token
from flaskel import httpcode


@auth.route('/access_token', methods=['POST'])
def access_token():
    """

    :return:
    """
    data = flask.request.json
    if data.email == 'email' and data.password == 'password':
        return create_tokens(data.email)

    flask.abort(httpcode.UNAUTHORIZED)


@auth.route('/refresh_token', methods=['GET'])
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
