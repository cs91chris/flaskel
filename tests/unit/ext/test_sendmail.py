from unittest.mock import MagicMock

from vbcore.tester.asserter import Asserter

from flaskel.ext.sendmail import ClientMail


def test_sendmail(flaskel_app, caplog):
    flaskel_app.config.MAIL_DEFAULT_SENDER = "sender@mail.com"
    client_mail = ClientMail()
    client_mail.send = MagicMock()
    client_mail.init_app(flaskel_app)

    with flaskel_app.app_context():
        client_mail.sendmail(
            subject="TEST MAIL",
            body="TEST BODY",
            recipients=["test@mail.com"],
            cc=["cc@mail.com"],
        )
        client_mail.send.assert_called_once()

    Asserter.assert_equals(len(caplog.records), 1)
    Asserter.assert_equals(caplog.records[0].levelname, "INFO")
