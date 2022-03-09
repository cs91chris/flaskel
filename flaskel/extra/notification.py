import typing as t

import sqlalchemy as sa
from pyfcm import FCMNotification
from pyfcm.errors import FCMError
from sqlalchemy.exc import SQLAlchemyError
from vbcore.datastruct import ObjectDict
from vbcore.db.support import SQLASupport


class DeviceModelMixin:
    token = sa.Column(sa.String(255), unique=True, nullable=False)
    user_agent = sa.Column(sa.String(255), nullable=False)


# TODO: convert to an extension
class NotificationHandler:
    def __init__(self, model, session, provider=None, dry_run: bool = False):
        """

        :param model: sqlalchemy model class, must have a token column
        :param session: sqlalchemy session
        :param provider: an object with app attribute reference of app instance (not current_app)
                         only if async methods are used (for background tasks)
        :param dry_run: perform but not send notification (test only)
        """
        self.provider = provider
        self.session = session
        self.model = model
        self.dry_run = dry_run
        self.sa_support = SQLASupport(self.model, self.session)

    def _with_app_context(self, f, *args, **kwargs):
        assert (
            self.provider is not None
        ), "you must pass a provider in order to user async methods"

        app = self.provider.app
        with app.app_context():
            return f(app, *args, **kwargs)

    def async_register_device(self, *args, **kwargs):
        return self._with_app_context(self.register_device, *args, **kwargs)

    def async_send_push_notification(self, *args, **kwargs):
        return self._with_app_context(self.send_push_notification, *args, **kwargs)

    def register_device(self, app, data: ObjectDict):
        try:
            self.sa_support.update_or_create(data, token=data.token)
            self.session.commit()
        except SQLAlchemyError as exc:
            app.logger.exception(exc)
            self.session.rollback()

    def get_tokens(self, user_ids: t.List[t.Union[int, str]]) -> t.List[str]:
        # TODO: find a way to avoid big user_ids list
        query = self.model.query.with_entities(self.model.token).where(
            self.model.user_id.in_(user_ids)
        )
        return [token[0] for token in query]

    def send_push_notification(
        self,
        app,
        title: str,
        message: str,
        tokens: t.Optional[t.List[str]] = None,
        user_ids: t.Optional[t.List[t.Union[int, str]]] = None,
        **kwargs,
    ):
        """

        :param app: flask app instance
        :param title: notification title
        :param message: notification message
        :param user_ids: list of user ids (optional)
        :param tokens: list of fcm tokens (optional)
        :param kwargs: passed to notify_multiple_devices
        :return:
        """
        service = FCMNotification(api_key=app.config.FCM_API_KEY)
        service.FCM_MAX_RECIPIENTS = app.config.FCM_MAX_RECIPIENTS

        if tokens is None:
            try:
                tokens = self.get_tokens(user_ids)
            except SQLAlchemyError as exc:  # pragma: no cover
                app.logger.exception(exc)
                return

        kwargs.setdefault("sound", "Default")
        kwargs.setdefault("dry_run", self.dry_run)

        try:
            res = service.notify_multiple_devices(
                tokens,
                message_title=title,
                message_body=message,
                **kwargs,
            )
            app.logger.debug(res)
        except FCMError as exc:  # pragma: no cover
            app.logger.exception(exc)
