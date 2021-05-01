try:
    from pyfcm import FCMNotification
    from pyfcm.errors import FCMError
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:
    FCMNotification = FCMError = None
    SQLAlchemyError = None


class NotificationHandler:
    def __init__(self, model, session, provider=None, dry_run=False):
        """

        :param model: sqlalchemy model class, must have a token column
        :param session: sqlalchemy session
        :param provider: an object with app attribute reference of app instance (nor current_app)
                         only if async methods are used (for background tasks)
        :param dry_run: perform but not send notification (test only)
        """
        self.provider = provider
        self.session = session
        self.model = model
        self.dry_run = dry_run

        assert FCMNotification is not None, "you must install 'pyfcm'"
        assert SQLAlchemyError is not None, "you must install 'sqlalchemy'"

    def _with_app_context(self, f, *args, **kwargs):
        assert self.provider is not None, "you must pass a provider in order to user async methods"

        app = self.provider.app
        with app.app_context():
            return f(app, *args, **kwargs)

    def async_register_device(self, *args, **kwargs):
        return self._with_app_context(self.register_device, *args, **kwargs)

    def async_send_push_notification(self, *args, **kwargs):
        return self._with_app_context(self.send_push_notification, *args, **kwargs)

    def register_device(self, app, data):
        try:
            device = self.model.query.filter_by(token=data['token']).first()
            if device:
                self.session.merge(device.update(data))
            else:
                self.session.add(self.model(**data))
            self.session.commit()
        except SQLAlchemyError as exc:  # pragma: no cover
            app.logger.exception(exc)
            self.session.rollback()

    def send_push_notification(self, app, title, message, user_ids=None, tokens=None, **kwargs):
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

        if tokens is None:
            try:
                tokens = self.model.query \
                    .with_entities(self.model.token) \
                    .where(self.model.user_id.in_(user_ids)) \
                    .all()
            except SQLAlchemyError as exc:  # pragma: no cover
                app.logger.exception(exc)
                return

        tokens = [t[0] for t in tokens]
        # noinspection PyUnresolvedReferences
        rmax = FCMNotification.FCM_MAX_RECIPIENTS - 1
        if len(tokens) > rmax:
            tokens_set = [tokens[x:x + rmax] for x in range(0, len(tokens), rmax)]
        else:
            tokens_set = tokens

        kwargs.setdefault('sound', 'Default')
        kwargs.setdefault('dry_run', self.dry_run)

        for ts in tokens_set:
            try:
                res = service.notify_multiple_devices(
                    ts, message_title=title, message_body=message, **kwargs
                )
                app.logger.debug(res)
            except FCMError as exc:  # pragma: no cover
                app.logger.exception(exc)
