import string
import typing as t

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode, HttpMethod
from vbcore.misc import random_string

from flaskel import (
    cap,
    abort,
    request,
    ConfigProxy,
    PayloadValidator,
    db_session,
    job_scheduler,
    client_redis,
)
from flaskel.ext.default import builder
from flaskel.views import BaseView


class AuthCode:
    def __init__(self, cache, config: ObjectDict):
        self.cache = cache
        self.sep = config.CACHE_KEY_SEPARATOR or "/"
        self.pre = config.CACHE_KEY_PREFIX or "auth_code//"
        self.expires = config.CACHE_TEMP_EXPIRES or 600
        self.key_format = f"{self.pre}{self.sep}{{key}}{self.sep}{{token}}"

    def generate(self, key, user):
        token = random_string(8, string.digits)
        cache_key = self.key_format.format(key=key, token=token)
        self.cache.set(cache_key, user.email, ex=self.expires)
        return token

    def check(self, key, token):
        cache_key = self.key_format.format(key=key, token=token)
        email = self.cache.get(cache_key)
        email = email.decode() if isinstance(email, bytes) else email
        self.cache.delete(cache_key)
        if not email:
            abort(httpcode.NOT_FOUND)
        return email


class AccountHandler:
    user_model = None  # type: ignore

    SCHEMAS = ObjectDict(
        register="REGISTER",
        register_confirm="REGISTER_CONFIRM",
        password_reset="PASSWORD_RESET",
        password_forgot="PASSWORD_FORGOT",
        password_confirm="PASSWORD_CONFIRM",
    )
    CACHE_TEMP_KEYS = ObjectDict(
        account_forgot="account_forgot",
        account_register="account_register",
    )

    def __init__(
        self,
        session=db_session,
        auth_code_handler: t.Optional[AuthCode] = None,
        notifications: t.Optional[ObjectDict] = None,
        scheduler=job_scheduler,
    ):
        self.session = session
        self.scheduler = scheduler
        self.auth_code_handler = auth_code_handler or AuthCode(
            client_redis, ObjectDict()
        )

        """ EXAMPLE
        ------------------------------------------------
            register:
              subject: Confirm your registration
              body: emails/registration.html
            forgot:
              subject: Forgot Password
              body: emails/forgot.html
        """
        self.notifications = notifications or ConfigProxy("NOTIFICATIONS")

    def send_notification(
        self, recipients: t.List[str], subject: str, template: str, **kwargs
    ):
        raise NotImplementedError

    def __check_user_model(self):
        if self.user_model is None:
            raise TypeError("user_model must be defined")
        return self.user_model

    @staticmethod
    def get_payload(schema: t.Union[str, dict]) -> ObjectDict:
        return PayloadValidator.validate(schema)

    def prepare_user(self, data: dict):
        user_model = self.__check_user_model()
        return user_model(**data)  # pylint: disable=not-callable

    def find_by_email(self, email: str):
        user_model = self.__check_user_model()
        return user_model.query.filter_by(email=email).first_or_404()

    def register(self):
        payload = self.get_payload(self.SCHEMAS.register)
        user = self.prepare_user(payload)

        try:
            self.session.add(user)
            self.session.commit()
        except Exception as exc:  # pylint: disable=broad-except
            cap.logger.exception(exc)
            self.session.rollback()
            abort(
                httpcode.CONFLICT
                if isinstance(exc, IntegrityError)
                else httpcode.INTERNAL_SERVER_ERROR
            )

        token = self.auth_code_handler.generate(
            self.CACHE_TEMP_KEYS.account_register, user
        )
        self.send_notification(
            recipients=[user.email],
            subject=self.notifications.register.subject,
            template=self.notifications.register.body,
            token=token,
            user=user.to_dict(),
        )

    def register_confirm(self):
        payload = self.get_payload(self.SCHEMAS.register_confirm)
        email = self.auth_code_handler.check(
            self.CACHE_TEMP_KEYS.account_register, payload.token
        )

        try:
            user = self.find_by_email(email)
            user.confirmed = True
            self.session.merge(user)
            self.session.commit()
        except SQLAlchemyError as exc:
            cap.logger.exception(exc)
            self.session.rollback()
            abort(httpcode.INTERNAL_SERVER_ERROR)

    def check_user(self, email: str, password: str):
        user = self.find_by_email(email)
        if not user.check_password(password):
            abort(httpcode.BAD_REQUEST)
        return user

    def password_reset(self):
        payload = self.get_payload(self.SCHEMAS.password_reset)
        user = self.check_user(payload.email, payload.old_password)
        try:
            user.password = payload.new_password
            self.session.merge(user)
            self.session.commit()
        except SQLAlchemyError as exc:
            cap.logger.exception(exc)
            self.session.rollback()
            abort(httpcode.INTERNAL_SERVER_ERROR)

    def password_forgot(self):
        payload = self.get_payload(self.SCHEMAS.password_forgot)
        user = self.find_by_email(payload.email)
        token = self.auth_code_handler.generate(
            self.CACHE_TEMP_KEYS.account_forgot, user
        )
        self.send_notification(
            recipients=[payload.email],
            subject=self.notifications.forgot.subject,
            template=self.notifications.forgot.body,
            token=token,
            user=user.to_dict(),
        )

    def password_confirm(self):
        payload = self.get_payload(self.SCHEMAS.password_confirm)
        email = self.auth_code_handler.check(
            self.CACHE_TEMP_KEYS.account_forgot, payload.token
        )
        user = self.find_by_email(email)
        user.password = payload.password

        try:
            self.session.merge(user)
            self.session.commit()
        except SQLAlchemyError as exc:
            cap.logger.exception(exc)
            self.session.rollback()
            abort(httpcode.INTERNAL_SERVER_ERROR)


class RegisterView(BaseView):
    account_handler: t.Type[AccountHandler] = AccountHandler

    default_view_name = "account_register"
    default_urls = ("/register",)
    methods = [
        HttpMethod.POST,
        HttpMethod.PUT,
    ]

    @builder.no_content
    def dispatch_request(self, *_, **__):
        if request.method == HttpMethod.POST:
            self.account_handler().register()
            return httpcode.ACCEPTED
        self.account_handler().register_confirm()
        return None


class PasswordForgotView(BaseView):
    account_handler: t.Type[AccountHandler] = AccountHandler

    default_view_name = "account_password_forgot"
    default_urls = ("/password/forgot",)
    methods = [
        HttpMethod.POST,
        HttpMethod.PUT,
    ]

    @builder.no_content
    def dispatch_request(self, *_, **__):
        if request.method == HttpMethod.POST:
            self.account_handler().password_forgot()
            return httpcode.ACCEPTED
        self.account_handler().password_confirm()
        return None


class PasswordResetView(BaseView):
    account_handler: t.Type[AccountHandler] = AccountHandler

    default_view_name = "account_password_reset"
    default_urls = ("/password/reset",)
    methods = [
        HttpMethod.POST,
    ]

    @builder.no_content
    def dispatch_request(self, *_, **__):
        self.account_handler().password_reset()
