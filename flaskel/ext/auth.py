import functools
from datetime import timedelta

import flask
import flask_jwt_extended as jwt
from flask_httpauth import HTTPBasicAuth

from flaskel.flaskel import cap, httpcode
from flaskel.utils.datastruct import ObjectDict
from .sqlalchemy import db
from .sqlalchemy.mixins import StandardMixin

jwtm = jwt.JWTManager()
basic_auth = HTTPBasicAuth()


@basic_auth.verify_password
def simple_basic_auth(username, password):
    if (
        username == cap.config.BASIC_AUTH_USERNAME
        and password == cap.config.BASIC_AUTH_PASSWORD
    ):
        return dict(username=username, password=password)
    return None


@jwtm.invalid_token_loader
def invalid_token_loader(mess):
    return dict(message=mess), httpcode.UNAUTHORIZED  # pragma: no cover


class RevokedTokenMixin(StandardMixin):
    jti = db.Column(db.String(120), nullable=False, unique=True)

    def __repr__(self):  # pragma: no cover
        return f"<RevokedToken: {self.id} - {self.jti}>"

    @classmethod
    def is_block_listed(cls, jti):  # pragma: no cover
        # noinspection PyUnresolvedReferences
        return bool(cls.query.filter_by(jti=jti).first())


class BaseTokenHandler:
    def __init__(self, blocklist_loader=None):
        """

        :param blocklist_loader:
        """
        jwtm.token_in_blocklist_loader(blocklist_loader)

    def check_token_block_listed(self, jwt_headers, jwt_data):
        raise NotImplementedError()  # pragma: no cover

    def revoke(self, token=None):
        raise NotImplementedError()  # pragma: no cover

    @classmethod
    def role(cls):
        return None  # pragma: no cover

    # noinspection PyMethodMayBeStatic
    def prepare_identity(self, data):  # pylint: disable=R0201
        return data

    @classmethod
    def check_permission(cls, role):
        if cls.role() != role:
            flask.abort(httpcode.FORBIDDEN)

    @classmethod
    def auth_required(cls, perm=None, **kwargs):
        def wrapper(fun):
            @functools.wraps(fun)
            @jwt.jwt_required(**kwargs)
            def check_optional_permission(*args, **kw):
                if perm is not None:
                    cls.check_permission(perm)
                return fun(*args, **kw)

            return check_optional_permission

        return wrapper

    @classmethod
    def identity(cls):
        identity = jwt.get_jwt_identity()
        if isinstance(identity, dict):
            identity = ObjectDict(**identity)
        return identity

    @classmethod
    def get_raw(cls):
        return ObjectDict(**jwt.get_jwt())

    @classmethod
    def decode(cls, token):
        return ObjectDict(**jwt.decode_token(token))

    def get_access(self, identity=None, expires=None):
        """

        :param identity:
        :param expires:
        :return:
        """
        return jwt.create_access_token(
            identity=identity or self.identity(),
            expires_delta=timedelta(expires) if expires else None,
        )

    def get_refresh(self, identity=None, expires=None):
        """

        :param identity:
        :param expires:
        :return:
        """
        return jwt.create_refresh_token(
            identity=identity or self.identity(),
            expires_delta=timedelta(expires) if expires else None,
        )

    def refresh(self, expires=None):
        """

        :param expires: in seconds
        :return:
        """
        access_token = self.get_access(expires=expires)
        decoded = self.decode(access_token)
        return ObjectDict(
            access_token=access_token,
            expires_in=decoded.exp,
            issued_at=decoded.iat,
            token_type=cap.config.JWT_DEFAULT_TOKEN_TYPE,
            scope=cap.config.JWT_DEFAULT_SCOPE,
        )

    def create(
        self,
        identity,
        refresh=True,
        expires_access=None,
        expires_refresh=None,
        scope=None,
    ):
        """

        :param identity: user identifier, generally the username
        :param refresh: enable refresh token
        :param expires_access: in seconds
        :param expires_refresh: in seconds
        :param scope:
        :return:
        """
        identity = self.prepare_identity(identity)
        access_token = self.get_access(identity=identity, expires=expires_access)
        decoded = self.decode(access_token)
        resp = ObjectDict(
            access_token=access_token,
            expires_in=decoded.exp,
            issued_at=decoded.iat,
            token_type=cap.config.JWT_DEFAULT_TOKEN_TYPE,
            scope=scope or cap.config.JWT_DEFAULT_SCOPE,
        )

        if refresh:
            resp.refresh_token = self.get_refresh(
                identity=identity, expires=expires_refresh
            )

        return resp

    def dump(self, token_type=None, scope=None):
        """

        :param token_type:
        :param scope:
        :return:
        """
        return ObjectDict(
            token_type=token_type or cap.config.JWT_DEFAULT_TOKEN_TYPE,
            scope=scope or cap.config.JWT_DEFAULT_SCOPE,
            **self.get_raw(),
        )


class DBTokenHandler(BaseTokenHandler):
    def __init__(self, model, session, blocklist_loader=None):
        """

        :param model:
        """
        self.model = model
        self.session = session
        super().__init__(blocklist_loader or self.check_token_block_listed)

    def check_token_block_listed(self, jwt_headers, jwt_data):
        """

        :param jwt_headers:
        :param jwt_data:
        :return:
        """
        return self.model.is_block_listed(jwt_data["jti"])

    def revoke(self, token=None):
        """

        :param token:
        """
        token = self.decode(token) if token else self.get_raw()
        if token.jti:
            self.session.add(self.model(jti=token.jti))
            self.session.commit()


class RedisTokenHandler(BaseTokenHandler):
    entry_value = "true"
    key_prefix = "token_revoked::"

    def __init__(self, redis, blocklist_loader=None):
        """

        :param redis:
        :param blocklist_loader:
        """
        self.redis = redis
        super().__init__(blocklist_loader or self.check_token_block_listed)

    def check_token_block_listed(self, jwt_headers, jwt_data):
        """

        :param jwt_headers:
        :param jwt_data:
        :return:
        """
        entry = self.redis.get(f"{self.key_prefix}{jwt_data['jti']}")
        if not entry:
            return False

        return entry == self.entry_value or entry == self.entry_value.encode()

    def revoke(self, token=None):
        """

        :param token:
        """
        token = self.decode(token) if token else self.get_raw()
        self.redis.set(f"{self.key_prefix}{token.jti}", self.entry_value)
