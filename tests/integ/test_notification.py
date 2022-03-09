from unittest.mock import patch, MagicMock

from vbcore.datastruct import ObjectDict
from vbcore.db.mixins import StandardMixin
from vbcore.tester.mixins import Asserter

from flaskel import db_session
from flaskel.ext.default import Database
from flaskel.extra.notification import NotificationHandler, DeviceModelMixin

db = Database()  # type: ignore


class Device(db.Model, StandardMixin, DeviceModelMixin):
    __tablename__ = "user_devices"

    user_id = db.Column(db.Integer())


def test_register_device(testapp):
    app = testapp(extensions={"database": db})
    notification = NotificationHandler(Device, db_session, provider=ObjectDict(app=app))

    notification.register_device(
        app,
        data=ObjectDict(
            token="test-token",
            user_agent="test-useragent",
            user_id=999,
        ),
    )
    notification.async_register_device(
        data=ObjectDict(
            token="test-token",
            user_agent="test-useragent",
            user_id=998,
        ),
    )
    notification.async_register_device(
        data=ObjectDict(token="test-token-error"),
    )

    devices = Device.query.all()
    Asserter.assert_equals(len(devices), 1)


@patch("flaskel.extra.notification.FCMNotification")
def test_notification(mock_fcm, testapp, session_save):
    mock_instance = MagicMock()
    mock_fcm.return_value = mock_instance

    app = testapp(
        config=ObjectDict(FCM_API_KEY="fake-api-key", FCM_MAX_RECIPIENTS=10),
        extensions={"database": db},
    )
    notification = NotificationHandler(Device, db_session, provider=ObjectDict(app=app))

    with app.app_context():
        session_save(
            [
                Device(id=1, token="token-1", user_agent="ua-1", user_id=1),
                Device(id=2, token="token-2", user_agent="ua-2", user_id=2),
                Device(id=3, token="token-3", user_agent="ua-3", user_id=3),
            ]
        )

    notification.send_push_notification(
        app,
        user_ids=[1, 2, 3],
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

    notification.async_send_push_notification(
        user_ids=[1, 2, 3],
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
