import socket
import typing as t

from flask_mail import Attachment, Mail, Message
from vbcore.datastruct import ObjectDict

AddressType = t.Union[str, t.Tuple[str, str]]


class ClientMail(Mail):
    def init_app(self, app):
        self.app = app
        super().init_app(app)
        app.extensions["client_mail"] = self

    @property
    def config(self) -> ObjectDict:
        return t.cast(ObjectDict, self.app.config)

    def sendmail(
        self,
        subject: str,
        html: t.Optional[str] = None,
        body: t.Optional[str] = None,
        recipients: t.Optional[t.List[AddressType]] = None,
        reply_to: t.Optional[AddressType] = None,
        cc: t.Optional[t.List[AddressType]] = None,
        bcc: t.Optional[t.List[AddressType]] = None,
        sender: t.Optional[AddressType] = None,
        attachments: t.Optional[t.List[Attachment]] = None,
        **kwargs,
    ) -> str:
        sender = sender or self.config.MAIL_DEFAULT_SENDER
        destination = recipients or [self.config.MAIL_RECIPIENT]
        message = Message(
            subject=subject,
            html=html,
            body=body,
            recipients=destination,
            reply_to=reply_to,
            cc=cc,
            bcc=bcc,
            sender=sender,
            attachments=attachments,
            **kwargs,
        )

        timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(self.config.MAIL_TIMEOUT or 60)
        self.send(message)
        socket.setdefaulttimeout(timeout)

        self.app.logger.info(
            "sent email %s from %s to %s", message.msgId, sender, destination
        )
        return message.msgId
