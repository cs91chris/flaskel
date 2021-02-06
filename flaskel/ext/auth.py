from datetime import timedelta

import flask_jwt_extended as jwt
from flask_httpauth import HTTPBasicAuth

from flaskel import cap, httpcode
from flaskel.utils.datastruct import ObjectDict
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
        return f"<RevokedToken: {self.id} - {self.jti}>"

    @classmethod
    def is_jti_blacklisted(cls, jti):  # pragma: no cover
        return bool(cls.query.filter_by(jti=jti).first())


@jwtm.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):  # pragma: no cover
    return RevokedTokenModel.is_jti_blacklisted(decrypted_token['jti'])


class TokenHandler:
    revoked_token_model = RevokedTokenModel

    @classmethod
    def identity(cls):
        return jwt.get_jwt_identity()

    @classmethod
    def decode(cls, token):
        return ObjectDict(**jwt.decode_token(token))

    @classmethod
    def get_raw(cls):
        return ObjectDict(**jwt.get_raw_jwt())

    @classmethod
    def get_access(cls, identity=None, expires=None):
        return jwt.create_access_token(
            identity=identity or cls.identity(),
            expires_delta=timedelta(expires) if expires else None
        )

    @classmethod
    def get_refresh(cls, identity=None, expires=None):
        return jwt.create_refresh_token(
            identity=identity or cls.identity(),
            expires_delta=timedelta(expires) if expires else None
        )

    @classmethod
    def refresh(cls, expires=None):
        """

        :param expires: in seconds
        :return:
        """
        access_token = cls.get_access(expires=expires)
        decoded = cls.decode(access_token)
        return ObjectDict(
            access_token=access_token,
            expires_in=decoded.exp,
            issued_at=decoded.iat,
            token_type=cap.config.JWT_DEFAULT_TOKEN_TYPE,
            scope=cap.config.JWT_DEFAULT_SCOPE
        )

    @classmethod
    def create(cls, identity, refresh=True, expires_access=None, expires_refresh=None, scope=None):
        """

        :param identity: user identifier, generally the username
        :param refresh: enable refresh token
        :param expires_access: in seconds
        :param expires_refresh: in seconds
        :param scope:
        :return:
        """
        access_token = cls.get_access(identity=identity, expires=expires_access)
        decoded = cls.decode(access_token)
        resp = ObjectDict(
            access_token=access_token,
            expires_in=decoded.exp,
            issued_at=decoded.iat,
            token_type=cap.config.JWT_DEFAULT_TOKEN_TYPE,
            scope=scope or cap.config.JWT_DEFAULT_SCOPE
        )

        if refresh:
            resp.refresh_token = cls.get_refresh(identity=identity, expires=expires_refresh)

        return resp

    @classmethod
    def revoke(cls, token=None):
        token = cls.decode(token) if token else cls.get_raw()
        if token.jti:
            cls.revoked_token_model(jti=token.jti).add()

    @classmethod
    def dump(cls):
        return ObjectDict(
            token_type=cap.config.JWT_DEFAULT_TOKEN_TYPE,
            scope=cap.config.JWT_DEFAULT_SCOPE,
            **cls.get_raw()
        )
