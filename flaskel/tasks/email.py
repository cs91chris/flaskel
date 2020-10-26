import socket

from flask_mail import Message

from flaskel import cap
from . import celery


@celery.task
def send_email(email_data):
    """

    :param email_data:
    """
    message = Message(
        email_data['subject'],
        sender=cap.config['MAIL_DEFAULT_SENDER'],
        recipients=[
            email_data['to']
        ]
    )
    message.body = email_data['body']
    mail = cap.extensions['mail']

    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(60)

    mail.send(message)
    socket.setdefaulttimeout(old_timeout)
