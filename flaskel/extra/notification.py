import typing as t

import sqlalchemy as sa
from pyfcm import FCMNotification as Firebase
from pyfcm.errors import FCMError
from sqlalchemy.exc import SQLAlchemyError
from vbcore.datastruct import ObjectDict
from vbcore.db.mixins import ExtraMixin
from vbcore.db.support import SQLASupport
from vbcore.http import HttpMethod
from vbcore.jsonschema.support import Fields
from vbcore.uuid import get_uuid

from flaskel import (
    db_session,
    ExtProxy,
    job_scheduler,
    PayloadValidator,
    request,
    Response,
)
from flaskel.views import BaseView


class SCHEMAS:
    DEVICE_REGISTER = Fields.object(properties={"token": Fields.string})
    SEND_PUSH = Fields.object(
        required=["title", "message"],
        properties={
            "title": Fields.string,
            "message": Fields.string,
            "tokens": Fields.oneof(Fields.array(items=Fields.string)),
            "user_ids": Fields.oneof(Fields.array(items=Fields.string)),
        },
    )


class DeviceModelMixin(ExtraMixin):
    token = sa.Column(sa.String(255), unique=True, nullable=False)
    user_id = sa.Column(sa.String(255), index=True, default=get_uuid())
    user_agent = sa.Column(sa.String(255), nullable=False)


class FCMNotification:
    def __init__(self, app=None, model=None, session=None, dry_run: bool = False):
        self.app = app
        self.model = model
        self.dry_run = dry_run
        self.service: Firebase
        self.sa_support: SQLASupport
        self.session = session or db_session

        if model is not None:
            self.sa_support = SQLASupport(self.model, self.session)

        if app is not None:
            self.init_app(app, model, session, dry_run)

    def init_app(self, app, model, session=None, dry_run: bool = False):
        self.app = app
        self.model = model
        self.session = session
        self.dry_run = dry_run
        self.sa_support = SQLASupport(self.model, self.session)
        self.service = Firebase(api_key=self.app.config.FCM_API_KEY)
        self.service.FCM_MAX_RECIPIENTS = self.app.config.FCM_MAX_RECIPIENTS
        app.extensions["fcm_notification"] = self

    def register_device(self, data: ObjectDict):
        try:
            self.sa_support.update_or_create(data, token=data.token)
            self.session.commit()
        except SQLAlchemyError as exc:
            self.app.logger.exception(exc)
            self.session.rollback()

    def get_tokens(self, user_ids: t.List[str]) -> t.List[str]:
        # TODO: find a way to avoid big user_ids list
        query = self.model.query.with_entities(self.model.token).where(
            self.model.user_id.in_(user_ids)
        )
        return [token[0] for token in query]

    def send_push_notification(
        self,
        title: str,
        message: str,
        tokens: t.Optional[t.List[str]] = None,
        user_ids: t.Optional[t.List[str]] = None,
        **kwargs,
    ):
        """

        :param title: notification title
        :param message: notification message
        :param user_ids: list of user ids (optional)
        :param tokens: list of fcm tokens (optional)
        :param kwargs: passed to notify_multiple_devices
        :return:
        """
        if tokens is None:
            if not user_ids:
                raise ValueError("one of 'tokens' or 'user_ids' must be given")
            try:
                tokens = self.get_tokens(user_ids)
            except SQLAlchemyError as exc:  # pragma: no cover
                self.app.logger.exception(exc)
                return None

        kwargs.setdefault("sound", "Default")
        kwargs.setdefault("dry_run", self.dry_run)

        try:
            return self.service.notify_multiple_devices(
                tokens,
                message_title=title,
                message_body=message,
                **kwargs,
            )
        except FCMError as exc:  # pragma: no cover
            self.app.logger.exception(exc)
            return None


class DeviceRegisterView(BaseView):
    methods = [HttpMethod.POST]
    default_view_name = "fcm_device_register"
    default_urls = ("/device/register",)
    handler = ExtProxy("fcm_notification")
    schema = "DEVICE_REGISTER"

    def get_user_id(self):
        """must be implemented in subclass"""
        return self.not_implemented()

    def dispatch_request(self, *_, **__):
        payload = PayloadValidator.validate(self.schema)
        payload.user_id = self.get_user_id()
        payload.useragent = request.user_agent.string
        job_scheduler.add(
            self.handler.register_device,
            args=(payload,),
        )
        return Response.no_content()


class SendPushView(BaseView):
    methods = [HttpMethod.POST]
    default_view_name = "fcm_send"
    default_urls = ("/send/push",)
    handler = ExtProxy("fcm_notification")
    schema = "SEND_PUSH"

    def dispatch_request(self, *_, **__):
        payload = PayloadValidator.validate(self.schema)
        job_scheduler.add(
            self.handler.send_push_notification,
            kwargs=payload,
        )
        return Response.no_content()
