import socket

try:
    from flask_mail import Mail, Message
except (ModuleNotFoundError, ImportError):
    Mail = Message = object


class ClientMail(Mail):
    def init_app(self, app):
        assert Mail is not object, "you must install 'flask_mail'"

        super().init_app(app)
        app.extensions = getattr(app, "extensions", {})
        app.extensions["client_mail"] = self

    def sendmail(
        self,
        app,
        sender=None,
        recipients=None,
        message=None,
        attachments=None,
        **kwargs,
    ):
        """

        :param app:
        :param message:
        :param sender:
        :param recipients:
        :param attachments:
        """
        destination = recipients or [app.config.MAIL_RECIPIENT]
        try:
            if sender.name and sender.surname:
                sender = (f"{sender.name} {sender.surname}", sender.email)
            else:
                sender = sender.email or app.config.MAIL_DEFAULT_SENDER
        except AttributeError:
            sender = sender or app.config.MAIL_DEFAULT_SENDER

        mail_message = Message(sender=sender, recipients=destination, **kwargs)
        mail_message.html = message

        if attachments:
            try:
                for attach in attachments:
                    with open(attach["filename"]) as file:
                        mail_message.attach(data=file.read(), **(attach or {}))
            except (OSError, IOError) as exc:
                app.logger.warning(str(exc))

        try:
            timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(app.config.MAIL_TIMEOUT or 60)

            with app.app_context():
                self.send(mail_message)

            socket.setdefaulttimeout(timeout)
        except OSError as exc:
            app.logger.exception(exc)

        app.logger.info(
            "email %s from %s sent to %s", mail_message.msgId, sender, destination
        )


client_mail = ClientMail()
