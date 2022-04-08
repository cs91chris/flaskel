import dataclasses
import functools
import typing as t
from datetime import timedelta

import sqlalchemy as sa
from flask_httpauth import HTTPBasicAuth
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
    JWTManager,
)
from vbcore.datastruct import DataClassDictable, ObjectDict
from vbcore.db.mixins import StandardMixin
from vbcore.http import httpcode

from flaskel.flaskel import cap
from flaskel.http.exceptions import abort

token_auth: JWTManager = JWTManager()
basic_auth: HTTPBasicAuth = HTTPBasicAuth()


@basic_auth.verify_password
def simple_basic_auth(username: str, password: str) -> t.Optional[dict]:
    if (
        username == cap.config.BASIC_AUTH_USERNAME
        and password == cap.config.BASIC_AUTH_PASSWORD
    ):
        return dict(username=username, password=password)
    return None


@token_auth.invalid_token_loader
def invalid_token_loader(mess) -> t.Tuple[dict, int]:
    return dict(message=mess), httpcode.UNAUTHORIZED


class RevokedTokenMixin(StandardMixin):
    jti = sa.Column(sa.String(120), nullable=False, unique=True)

    def __repr__(self):
        return f"<RevokedToken: {self.id} - {self.jti}>"

    @classmethod
    def is_block_listed(cls, jti: str) -> bool:
        # noinspection PyUnresolvedReferences
        return bool(cls.query.filter_by(jti=jti).first())


@dataclasses.dataclass(frozen=True)
class TokenInfo(DataClassDictable):
    fresh: bool
    expires_in: int
    issued_at: int
    token_type: str
    type: str
    jti: str
    identity: dict
    scope: t.Optional[str] = None


@dataclasses.dataclass(frozen=True)
class TokenData(DataClassDictable):
    access_token: str
    expires_in: int
    issued_at: int
    token_type: str
    scope: t.Optional[str] = None
    refresh_token: t.Optional[str] = None

    def to_dict(self, **kwargs) -> ObjectDict:
        data = ObjectDict(
            access_token=self.access_token,
            expires_in=self.expires_in,
            issued_at=self.issued_at,
            token_type=self.token_type,
            scope=self.scope,
            **kwargs,
        )
        if self.refresh_token:
            data.refresh_token = self.refresh_token
        return data


class BaseTokenHandler:
    def __init__(self, blocklist_loader: t.Optional[t.Callable] = None):
        token_auth.token_in_blocklist_loader(blocklist_loader)

    # pylint: disable=no-self-use
    def check_token_block_listed(self, jwt_headers, jwt_data) -> bool:
        _ = jwt_headers, jwt_data
        return False

    def revoke(self, token: t.Optional[str] = None):
        """can be implemented by subclass"""

    @classmethod
    def role(cls):
        return None

    # noinspection PyMethodMayBeStatic
    def prepare_identity(self, data):  # pylint: disable=no-self-use
        return data

    @classmethod
    def check_permission(cls, role):
        if cls.role() != role:
            abort(httpcode.FORBIDDEN)

    @classmethod
    def auth_required(cls, perm=None, **kwargs):
        def wrapper(fun):
            @functools.wraps(fun)
            @jwt_required(**kwargs)
            def check_optional_permission(*args, **kw):
                if perm is not None:
                    cls.check_permission(perm)
                return fun(*args, **kw)

            return check_optional_permission

        return wrapper

    @classmethod
    def identity(cls) -> ObjectDict:
        identity = get_jwt_identity()
        if isinstance(identity, dict):
            identity = ObjectDict(**identity)
        return identity

    @classmethod
    def get_raw(cls) -> ObjectDict:
        return ObjectDict(**get_jwt())

    @classmethod
    def decode(cls, token: str) -> ObjectDict:
        return ObjectDict(**decode_token(token))

    def get_access(self, identity=None, expires: t.Optional[int] = None) -> str:
        return create_access_token(
            identity=identity or self.identity(),
            expires_delta=timedelta(seconds=expires) if expires else None,
        )

    def get_refresh(self, identity=None, expires: t.Optional[int] = None) -> str:
        return create_refresh_token(
            identity=identity or self.identity(),
            expires_delta=timedelta(seconds=expires) if expires else None,
        )

    def refresh(self, expires: t.Optional[int] = None) -> TokenData:
        access_token = self.get_access(expires=expires)
        decoded = self.decode(access_token)
        return TokenData(
            access_token=access_token,
            expires_in=decoded.exp,
            issued_at=decoded.iat,
            token_type=cap.config.JWT_DEFAULT_TOKEN_TYPE,
            scope=cap.config.JWT_DEFAULT_SCOPE,
        )

    def create(
        self,
        identity,
        refresh: bool = True,
        expires_access: t.Optional[int] = None,
        expires_refresh: t.Optional[int] = None,
        scope: t.Optional[str] = None,
    ) -> TokenData:
        identity = self.prepare_identity(identity)
        access_token = self.get_access(identity=identity, expires=expires_access)
        decoded = self.decode(access_token)
        return TokenData(
            access_token=access_token,
            expires_in=decoded.exp,
            issued_at=decoded.iat,
            token_type=cap.config.JWT_DEFAULT_TOKEN_TYPE,
            scope=scope or cap.config.JWT_DEFAULT_SCOPE,
            refresh_token=self.get_refresh(identity=identity, expires=expires_refresh)
            if refresh
            else None,
        )

    def dump(self) -> TokenInfo:
        data = self.get_raw()
        return TokenInfo(
            fresh=data.fresh,
            type=data.type,
            token_type=data.token_type,
            scope=data.scope,
            expires_in=data.exp,
            issued_at=data.iat,
            jti=data.jti,
            identity=data.identity,
        )


class DBTokenHandler(BaseTokenHandler):
    def __init__(self, model, session, blocklist_loader: t.Optional[t.Callable] = None):
        self.model = model
        self.session = session
        super().__init__(blocklist_loader or self.check_token_block_listed)

    def check_token_block_listed(self, jwt_headers, jwt_data) -> bool:
        return self.model.is_block_listed(jwt_data["jti"])

    def revoke(self, token: t.Optional[str] = None):
        decoded_token = self.decode(token) if token else self.get_raw()
        if decoded_token.jti:
            self.session.add(self.model(jti=decoded_token.jti))
            self.session.commit()


class RedisTokenHandler(BaseTokenHandler):
    entry_value = "true"
    key_prefix = "token_revoked::"

    def __init__(self, redis, blocklist_loader: t.Optional[t.Callable] = None):
        self.redis = redis
        super().__init__(blocklist_loader or self.check_token_block_listed)

    def check_token_block_listed(self, jwt_headers, jwt_data) -> bool:
        entry = self.redis.get(f"{self.key_prefix}{jwt_data['jti']}")
        if not entry:
            return False

        if isinstance(entry, str):
            return entry == self.entry_value
        return entry == self.entry_value.encode()

    def revoke(self, token: t.Optional[str] = None):
        decoded_token = self.decode(token) if token else self.get_raw()
        self.redis.set(f"{self.key_prefix}{decoded_token.jti}", self.entry_value)
