from unittest.mock import patch, MagicMock

from vbcore.datastruct import ObjectDict
from vbcore.db.mixins import StandardMixin
from vbcore.http import httpcode
from vbcore.http.headers import HeaderEnum
from vbcore.tester.mixins import Asserter

from flaskel import db_session, ExtProxy
from flaskel.ext.default import Database, Scheduler
from flaskel.extra.notification import (
    FCMNotification,
    DeviceModelMixin,
    DeviceRegisterView as BaseDeviceRegisterView,
    SendPushView,
    SCHEMAS,
)
from flaskel.tester.helpers import ApiTester

db = Database()
notification = ExtProxy("fcm_notification")

VIEW_CONFIG = ObjectDict(
    SCHEMAS=ObjectDict(
        DEVICE_REGISTER=SCHEMAS.DEVICE_REGISTER,
        SEND_PUSH=SCHEMAS.SEND_PUSH,
    ),
    FCM_API_KEY="fake-api-key",
)


class Device(db.Model, StandardMixin, DeviceModelMixin):
    __tablename__ = "user_devices"


class DeviceRegisterView(BaseDeviceRegisterView):
    def get_user_id(self):
        return 1


EXTENSIONS = {
    "database": db,
    "scheduler": Scheduler(),
    "notification": (
        FCMNotification(),
        {
            "model": Device,
            "session": db_session,
        },
    ),
}


def test_register_device(testapp):
    testapp(config=ObjectDict(FCM_API_KEY="fake-api-key"), extensions=EXTENSIONS)

    notification.register_device(
        data=ObjectDict(
            token="test-token",
            user_agent="test-useragent",
            user_id="999",
        ),
    )
    notification.register_device(
        data=ObjectDict(
            token="test-token",
            user_agent="test-useragent",
            user_id="998",
        ),
    )
    notification.register_device(
        data=ObjectDict(token="test-token-error"),
    )

    devices = Device.query.all()
    Asserter.assert_equals(len(devices), 1)


@patch("flaskel.extra.notification.Firebase")
def test_notification(mock_fcm, testapp, session_save):
    mock_instance = MagicMock()
    mock_fcm.return_value = mock_instance

    app = testapp(
        config=ObjectDict(FCM_API_KEY="fake-api-key", FCM_MAX_RECIPIENTS=10),
        extensions=EXTENSIONS,
    )

    with app.app_context():
        session_save(
            [
                Device(id=1, token="token-1", user_agent="ua-1", user_id="1"),
                Device(id=2, token="token-2", user_agent="ua-2", user_id="2"),
                Device(id=3, token="token-3", user_agent="ua-3", user_id="3"),
            ]
        )

    notification.send_push_notification(
        user_ids=["1", "2", "3"],
        title="Title",
        message="Message",
    )
    mock_instance.notify_multiple_devices.assert_called_with(
        ["token-1", "token-2", "token-3"],
        message_title="Title",
        message_body="Message",
        sound="Default",
        dry_run=False,
    )


def test_register_device_view(testapp):
    app = testapp(
        config=VIEW_CONFIG, extensions=EXTENSIONS, views=(DeviceRegisterView,)
    )
    client = ApiTester(app.test_client())

    client.post(
        view=DeviceRegisterView.default_view_name,
        headers={HeaderEnum.USER_AGENT: "test-useragent"},
        status=httpcode.NO_CONTENT,
        json={"token": "test-token"},
    )


def test_send_push_view(testapp):
    app = testapp(config=VIEW_CONFIG, extensions=EXTENSIONS, views=(SendPushView,))
    client = ApiTester(app.test_client())

    client.post(
        view=SendPushView.default_view_name,
        status=httpcode.NO_CONTENT,
        json={
            "title": "Title",
            "message": "Message",
            "user_ids": ["1", "2", "3"],
        },
    )
