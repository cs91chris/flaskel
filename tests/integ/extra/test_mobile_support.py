from redislite import StrictRedis
from vbcore.http import httpcode
from vbcore.http.headers import ContentTypeEnum
from vbcore.tester.mixins import Asserter

from flaskel.extra.mobile_support import (
    MobileLoggerView,
    MobileReleaseView,
    MobileVersionCompatibility,
    RedisStore,
)
from flaskel.tester.helpers import ApiTester, url_for
from tests.integ.views import bp_api

MOBILE_EXT = {
    "mobile": (
        MobileVersionCompatibility(),
        dict(store=RedisStore(StrictRedis("/tmp/redis.db"))),
    )
}


def test_mobile_logger_view(testapp):
    app = testapp(views=(MobileLoggerView,))
    client = ApiTester(app.test_client())

    view = MobileLoggerView.default_view_name
    data = {"stacktrace": "exception"}

    client.post(view=view, json=data, status=httpcode.NO_CONTENT)
    res = client.post(view=view, json=data, params={"debug": "true"})
    Asserter.assert_equals(res.json, data)


def test_mobile_release(testapp):
    version = "1.0.0"
    agent = {"agent": "ios"}
    app = testapp(views=((MobileReleaseView, bp_api),), extensions=MOBILE_EXT)
    view = f"api.{MobileReleaseView.default_view_name}"
    client = ApiTester(app.test_client())

    client.delete(url=url_for(view, **agent))
    client.delete(url=url_for(view, all="true", **agent), status=httpcode.NO_CONTENT)

    res = client.post(url=url_for(view, ver=version, **agent))
    Asserter.assert_equals(len(res.json), 1)
    Asserter.assert_allin(res.json[0], ("critical", "version"))

    res = client.get(url=url_for(view, all="true", **agent))
    Asserter.assert_allin(res.json[0], ("critical", "version"))

    client.post(url=url_for(view, ver=version, **agent), status=httpcode.BAD_REQUEST)
    res = client.get(url=url_for(view, ver="latest", **agent))
    Asserter.assert_content_type(res, ContentTypeEnum.PLAIN)
    Asserter.assert_equals(res.data, version.encode())


def test_mobile_version(testapp):
    agent = {"agent": "ios"}
    app = testapp(views=(MobileReleaseView,), extensions=MOBILE_EXT)
    view = MobileReleaseView.default_view_name
    client = ApiTester(app.test_client())

    upgrade_header = app.config.VERSION_UPGRADE_HEADER
    version_header = app.config.VERSION_API_HEADER
    mobile_version = app.config.VERSION_HEADER_KEY
    agent_header = app.config.VERSION_AGENT_HEADER

    headers = {agent_header: "ios"}
    res = client.get(
        view=view, headers={mobile_version: "0.0.0", **headers}, params=agent
    )
    Asserter.assert_header(res, upgrade_header, "0")
    Asserter.assert_header(res, version_header, "1.0.0")

    client.post(
        url=url_for(view, ver="1.0.1", critical="true", agent="ios"), headers=headers
    )
    res = client.get(
        view=view, headers={mobile_version: "0.0.0", **headers}, params=agent
    )
    Asserter.assert_header(res, upgrade_header, "1")

    res = client.get("/web-page-not-found", status=httpcode.NOT_FOUND)
    Asserter.assert_not_in(upgrade_header, list(res.headers.keys()))
    Asserter.assert_not_in(version_header, list(res.headers.keys()))
