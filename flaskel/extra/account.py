import string
import typing as t

import sqlalchemy as sa
from flask import render_template
from sqlalchemy.exc import SQLAlchemyError
from vbcore.datastruct import ObjectDict
from vbcore.db.exceptions import DBDuplicateEntry
from vbcore.db.mixins import StandardMixin, UserMixin
from vbcore.http import httpcode, HttpMethod
from vbcore.jsonschema.support import Fields
from vbcore.misc import random_string

from flaskel import (
    abort,
    cap,
    client_mail,
    client_redis,
    db_session,
    ExtProxy,
    job_scheduler,
    PayloadValidator,
    request,
    Response,
)
from flaskel.views import BaseView


class AccountModel(UserMixin, StandardMixin):
    is_active = sa.Column(sa.Boolean, default=False)
    is_confirmed = sa.Column(sa.Boolean, default=False)

    def to_dict(self):
        return ObjectDict(
            email=self.email,
            is_active=self.is_active,
            created_at=self.created_at,
        )


class AuthCode:
    def __init__(self, cache, prefix: str = "auth_code//", expires: int = 600):
        self.cache = cache
        self.expires = expires
        self.key_format = f"{prefix}/{{key}}/{{token}}"

    @classmethod
    def token_value(cls, length: int = 8) -> str:
        return random_string(length, string.digits)

    def generate(self, key: str, user: AccountModel) -> str:
        token = self.token_value()
        cache_key = self.key_format.format(key=key, token=token)
        self.cache.set(cache_key, user.email, ex=self.expires)
        return token

    def check(self, key: str, token: str) -> str:
        cache_key = self.key_format.format(key=key, token=token)
        email = self.cache.get(cache_key)
        email = email.decode() if isinstance(email, bytes) else email
        self.cache.delete(cache_key)
        if not email:
            abort(httpcode.NOT_FOUND)
        return email


class AccountHandler:
    session = db_session
    scheduler = job_scheduler
    client_mail = client_mail
    auth_code_handler_class = AuthCode

    CACHE_TEMP_KEYS = ObjectDict(
        account_forgot="account_forgot",
        account_register="account_register",
    )

    NOTIFICATIONS = ObjectDict(
        register={
            "subject": "Confirm your registration",
            "body": "emails/registration.html",
        },
        forgot={
            "subject": "Forgot Password",
            "body": "emails/forgot.html",
        },
    )

    def __init__(
        self,
        app=None,
        model=AccountModel,
        auth_code_handler: t.Optional[AuthCode] = None,
        **kwargs,
    ):
        self.model = model
        self.auth_code_handler = auth_code_handler or self.auth_code_handler_class(
            client_redis, **kwargs
        )

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault("NOTIFICATIONS", self.NOTIFICATIONS)
        app.extensions["account"] = self

    @classmethod
    def sendmail(cls, recipients: t.List[str], subject: str, template: str, **kwargs):
        cls.client_mail.sendmail(
            subject=subject,
            recipients=recipients,
            html=render_template(template, **kwargs),
        )

    def prepare_user(self, data: dict):
        return self.model(**data)

    def find_by_email(self, email: str):
        # noinspection PyUnresolvedReferences
        return self.model.query.filter_by(email=email).first_or_404()

    def register(self, payload: ObjectDict):
        user = self.prepare_user(payload)

        try:
            self.session.add(user)
            self.session.commit()
        except Exception as exc:  # pylint: disable=broad-except
            cap.logger.exception(exc)
            self.session.rollback()
            if isinstance(exc, DBDuplicateEntry):
                # TODO: return the duplicated keys
                abort(httpcode.CONFLICT)
            abort(httpcode.INTERNAL_SERVER_ERROR)

        token = self.auth_code_handler.generate(
            self.CACHE_TEMP_KEYS.account_register, user
        )
        self.sendmail(
            recipients=[user.email],
            subject=cap.config.NOTIFICATIONS.register.subject,
            template=cap.config.NOTIFICATIONS.register.body,
            token=token,
            user=user.to_dict(),
        )

    def register_confirm(self, payload: ObjectDict):
        email = self.auth_code_handler.check(
            self.CACHE_TEMP_KEYS.account_register, payload.token
        )

        try:
            user = self.find_by_email(email)
            user.is_active = True
            user.is_confirmed = True
            self.session.merge(user)
            self.session.commit()
        except SQLAlchemyError as exc:
            cap.logger.exception(exc)
            self.session.rollback()
            abort(httpcode.INTERNAL_SERVER_ERROR)

    def check_user(self, email: str, password: str):
        user = self.find_by_email(email)
        if not user.check_password(password):
            abort(httpcode.BAD_REQUEST, "invalid password")
        return user

    def password_reset(self, data: ObjectDict):
        user = self.check_user(data.email, data.old_password)
        try:
            user.password = data.new_password
            self.session.merge(user)
            self.session.commit()
        except SQLAlchemyError as exc:
            cap.logger.exception(exc)
            self.session.rollback()
            abort(httpcode.INTERNAL_SERVER_ERROR)

    def password_forgot(self, data: ObjectDict):
        user = self.find_by_email(data.email)
        token = self.auth_code_handler.generate(
            self.CACHE_TEMP_KEYS.account_forgot, user
        )
        self.sendmail(
            recipients=[data.email],
            subject=cap.config.NOTIFICATIONS.forgot.subject,
            template=cap.config.NOTIFICATIONS.forgot.body,
            token=token,
            user=user.to_dict(),
        )

    def password_confirm(self, data: ObjectDict):
        email = self.auth_code_handler.check(
            self.CACHE_TEMP_KEYS.account_forgot, data.token
        )
        user = self.find_by_email(email)
        user.password = data.password

        try:
            self.session.merge(user)
            self.session.commit()
        except SQLAlchemyError as exc:
            cap.logger.exception(exc)
            self.session.rollback()
            abort(httpcode.INTERNAL_SERVER_ERROR)


class BaseAccountView(BaseView):
    account_handler: AccountHandler = t.cast(AccountHandler, ExtProxy("account"))
    methods = [
        HttpMethod.POST,
        HttpMethod.PUT,
    ]

    DEFAULT_SCHEMAS = ObjectDict(
        REGISTER=Fields.object(
            properties={"email": Fields.string, "password": Fields.string}
        ),
        REGISTER_CONFIRM=Fields.object(properties={"token": Fields.string}),
        PASSWORD_RESET=Fields.object(
            properties={
                "email": Fields.string,
                "new_password": Fields.string,
                "old_password": Fields.string,
            }
        ),
        PASSWORD_FORGOT=Fields.object(properties={"email": Fields.string}),
        PASSWORD_CONFIRM=Fields.object(
            properties={"token": Fields.string, "password": Fields.string}
        ),
    )

    def __init__(self):
        self.schemas = cap.config.SCHEMAS.ACCOUNT or self.DEFAULT_SCHEMAS

    def get_payload(self, name: str) -> ObjectDict:
        return PayloadValidator.validate(self.schemas[name])


class RegisterView(BaseAccountView):
    default_view_name = "account_register"
    default_urls = ("/register",)

    def dispatch_request(self, *_, **__):
        if request.method == HttpMethod.POST:
            self.account_handler.register(self.get_payload("REGISTER"))
            return Response.no_content(httpcode.ACCEPTED)

        if request.method == HttpMethod.PUT:
            self.account_handler.register_confirm(self.get_payload("REGISTER_CONFIRM"))
            return Response.no_content()

        return abort(httpcode.METHOD_NOT_ALLOWED)


class PasswordForgotView(BaseAccountView):
    default_view_name = "account_password_forgot"
    default_urls = ("/password/forgot",)

    def dispatch_request(self, *_, **__):
        if request.method == HttpMethod.POST:
            self.account_handler.password_forgot(self.get_payload("PASSWORD_FORGOT"))
            return Response.no_content(httpcode.ACCEPTED)

        if request.method == HttpMethod.PUT:
            self.account_handler.password_confirm(self.get_payload("PASSWORD_CONFIRM"))
            return Response.no_content()

        return abort(httpcode.METHOD_NOT_ALLOWED)


class PasswordResetView(BaseAccountView):
    default_view_name = "account_password_reset"
    default_urls = ("/password/reset",)

    def dispatch_request(self, *_, **__):
        self.account_handler.password_reset(self.get_payload("PASSWORD_RESET"))
        return Response.no_content()
