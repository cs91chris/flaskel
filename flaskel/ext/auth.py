from datetime import timedelta

import flask_jwt_extended as jwt
from flask_httpauth import HTTPBasicAuth

from flaskel import cap, httpcode
from .sqlalchemy import db

jwtm = jwt.JWTManager()
basic_auth = HTTPBasicAuth()


@basic_auth.verify_password
def simple_basic_auth(username, password):
    if username == cap.config.BASIC_AUTH_USERNAME \
            and password == cap.config.BASIC_AUTH_PASSWORD:
        return dict(username=username, password=password)


@jwtm.invalid_token_loader
def invalid_token_loader(mess):
    return dict(message=mess), httpcode.UNAUTHORIZED  # pragma: no cover


class RevokedTokenModel(db.Model):
    __tablename__ = 'revoked_tokens'

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(120), nullable=False, unique=True)

    def __repr__(self):  # pragma: no cover
        return "<RevokedToken: %r>" % self.jti

    @classmethod
    def is_jti_blacklisted(cls, jti):  # pragma: no cover
        return bool(cls.query.filter_by(jti=jti).first())


@jwtm.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):  # pragma: no cover
    return RevokedTokenModel.is_jti_blacklisted(decrypted_token['jti'])


def refresh_access_token(expires=None):
    """

    :param expires: in seconds
    :return:
    """
    access_token = jwt.create_access_token(
        identity=jwt.get_jwt_identity(),
        expires_delta=timedelta(expires) if expires else None
    )
    decoded = jwt.decode_token(access_token)
    return dict(
        access_token=access_token,
        expires_in=decoded['exp'],
        issued_at=decoded['iat'],
        token_type=cap.config.JWT_DEFAULT_TOKEN_TYPE,
        scope=cap.config.JWT_DEFAULT_SCOPE
    )


def create_tokens(identity, expires_access=None, expires_refresh=None, scope=None):
    """

    :param identity: user identifier, generally the username
    :param expires_access: in seconds
    :param expires_refresh: in seconds
    :param scope:
    :return:
    """
    expires = timedelta(expires_access) if expires_access else None
    access_token = jwt.create_access_token(
        identity=identity, expires_delta=expires
    )

    expires = timedelta(expires_refresh) if expires_refresh else None
    refresh_token = jwt.create_refresh_token(
        identity=identity, expires_delta=expires
    )

    decoded = jwt.decode_token(access_token)
    expires_in = decoded['exp']
    issued_at = decoded['iat']

    return dict(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        issued_at=issued_at,
        token_type=cap.config.JWT_DEFAULT_TOKEN_TYPE,
        scope=scope or cap.config.JWT_DEFAULT_SCOPE
    )
