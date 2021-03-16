import socket

from flask_mail import Mail, Message


class ClientMail(Mail):
    def init_app(self, app):
        super().init_app(app)

        app.extensions = getattr(app, 'extensions', {})
        app.extensions['mail'] = self

    def sendmail(self, app, sender=None, recipients=None, message=None, attachments=None, **kwargs):
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
                    with open(attach['filename']) as f:
                        mail_message.attach(data=f.read(), **(attach or {}))
            except (OSError, IOError) as exc:
                app.logger.warning(str(exc))

        try:
            socket.setdefaulttimeout(app.config.MAIL_TIMEOUT or 60)
            with app.app_context():
                self.send(mail_message)
        except OSError as exc:
            app.logger.exception(exc)

        app.logger.info(f"email {mail_message.msgId} from {sender} sent to {destination}")


client_mail = ClientMail()
