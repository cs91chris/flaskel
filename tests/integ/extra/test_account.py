import re

from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode
from vbcore.http.headers import ContentTypeEnum
from vbcore.tester.mixins import Asserter

from flaskel import client_mail
from flaskel.ext.default import Database, client_redis
from flaskel.ext.sendmail import ClientMail
from flaskel.extra.account import (
    RegisterView,
    PasswordForgotView,
    PasswordResetView,
    AccountHandler,
    AccountModel as BaseAccountModel,
)
from flaskel.tester.helpers import ApiTester
from tests.integ.views import bp_api

db = Database()


class AccountModel(db.Model, BaseAccountModel):
    __tablename__ = "account"


EXTENSIONS = {
    "database": db,
    "redis": client_redis,
    "client_mail": ClientMail(),
    "account": AccountHandler(model=AccountModel),
}


class TestData:
    ACCOUNT = ObjectDict(
        email="register@test.com",
        password="test",
    )
    RESET = ObjectDict(
        email="register@test.com",
        old_password="test",
        new_password="new password",
    )


class Views:
    register = "api.account_register"
    password_reset = "api.account_password_reset"
    password_forgot = "api.account_password_forgot"


def grep_token_from_email(emails):
    content = emails[0].html
    tmp = re.findall(r"<span>(\d+)</span>", content)
    return tmp[0] if len(tmp) else None


def test_register(testapp):
    app = testapp(
        extensions=EXTENSIONS,
        views=((RegisterView, bp_api),),
    )
    client = ApiTester(app.test_client(), mimetype=ContentTypeEnum.JSON)

    with client_mail.record_messages() as outbox:
        client.post(
            view=Views.register,
            json=TestData.ACCOUNT,
            status=httpcode.ACCEPTED,
        )
        Asserter.assert_equals(len(outbox), 1)

    subject = app.config.NOTIFICATIONS.register.subject
    Asserter.assert_equals(outbox[0].subject, subject)
    Asserter.assert_equals(outbox[0].sender, app.config.MAIL_DEFAULT_SENDER)
    Asserter.assert_equals(outbox[0].recipients, [TestData.ACCOUNT.email])

    client.post(
        view=Views.register,
        json=TestData.ACCOUNT,
        status=httpcode.CONFLICT,
        mimetype=ContentTypeEnum.JSON_PROBLEM,
    )

    client.put(
        view=Views.register,
        json=dict(token=grep_token_from_email(outbox)),
        status=httpcode.NO_CONTENT,
    )


def test_password(testapp):
    app = testapp(
        extensions=EXTENSIONS,
        views=(
            (PasswordForgotView, bp_api),
            (PasswordResetView, bp_api),
        ),
    )
    client = ApiTester(app.test_client(), mimetype=ContentTypeEnum.JSON)

    client.post(
        view=Views.password_reset,
        json=TestData.RESET,
        status=httpcode.NO_CONTENT,
    )

    with client_mail.record_messages() as outbox:
        client.post(
            view=Views.password_forgot,
            json=dict(email=TestData.RESET.email),
            status=httpcode.ACCEPTED,
        )
        Asserter.assert_equals(len(outbox), 1)

    subject = app.config.NOTIFICATIONS.forgot.subject
    Asserter.assert_equals(outbox[0].subject, subject)
    Asserter.assert_equals(outbox[0].sender, app.config.MAIL_DEFAULT_SENDER)
    Asserter.assert_equals(outbox[0].recipients, [TestData.ACCOUNT.email])

    token = grep_token_from_email(outbox)
    client.put(
        view=Views.password_forgot,
        json=dict(token=token, password="new password"),
        status=httpcode.NO_CONTENT,
    )
