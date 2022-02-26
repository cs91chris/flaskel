from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode, HttpMethod
from vbcore.tester.mixins import Asserter
from werkzeug.exceptions import HTTPException

from flaskel import FlaskelHttp, FlaskelHttpBatch
from flaskel.http.client import HTTPStatusError

HOSTS = ObjectDict(
    apitester="http://httpbin.org",
    fake="http://localhost",
)


def test_utils_http_client_simple(flaskel_app):
    with flaskel_app.test_request_context():
        api = FlaskelHttp(HOSTS.apitester, token="pippo", dump_body=True)
        res = api.delete("/status/202")
        Asserter.assert_equals(res.status, httpcode.ACCEPTED)
        res = api.patch("/status/400")
        Asserter.assert_equals(res.status, httpcode.BAD_REQUEST)


def test_utils_http_client_exception(flaskel_app):
    logger = flaskel_app.logger
    api = FlaskelHttp(HOSTS.apitester, token="pippo", raise_on_exc=True, logger=logger)
    fake_api = FlaskelHttp(HOSTS.fake, username="test", password="test", logger=logger)

    with flaskel_app.test_request_context():
        res = fake_api.put("/", timeout=0.1)
        Asserter.assert_equals(res.status, httpcode.SERVICE_UNAVAILABLE)
        try:
            api.request("/status/500", method=HttpMethod.PUT)
        except HTTPStatusError as exc:
            Asserter.assert_equals(
                exc.response.status_code, httpcode.INTERNAL_SERVER_ERROR
            )
        try:
            fake_api.request("/", timeout=0.1)
        except HTTPException as exc:
            Asserter.assert_equals(exc.code, httpcode.INTERNAL_SERVER_ERROR)


def test_utils_http_client_filename(flaskel_app):
    filename = "pippo.txt"
    hdr = "Content-Disposition"
    param = {hdr: None}

    with flaskel_app.test_request_context():
        api = FlaskelHttp(HOSTS.apitester, dump_body=True)
        res = api.get("/not-found")
        Asserter.assert_status_code(res, httpcode.NOT_FOUND)

        param[hdr] = f"attachment; filename={filename}"
        res = api.get("/response-headers", params=param)
        Asserter.assert_equals(api.response_filename(res.headers), filename)

        param[hdr] = f"filename={filename}"
        res = api.post("/response-headers", params=param)
        Asserter.assert_equals(api.response_filename(res.headers), filename)

        param[hdr] = filename
        res = api.post("/response-headers", params=param)
        Asserter.assert_none(api.response_filename(res.headers))


def test_http_client_batch(flaskel_app):
    with flaskel_app.test_request_context():
        responses = FlaskelHttpBatch(
            logger=flaskel_app.logger, dump_body=(True, False)
        ).request(
            [
                dict(
                    url=f"{HOSTS.apitester}/anything",
                    method=HttpMethod.GET,
                    headers={"HDR1": "HDR1"},
                ),
                dict(
                    url=f"{HOSTS.apitester}/status/{httpcode.NOT_FOUND}",
                    method=HttpMethod.GET,
                ),
                dict(url=HOSTS.fake, method=HttpMethod.GET, timeout=0.1),
            ]
        )
    Asserter.assert_equals(responses[0].body.headers.Hdr1, "HDR1")
    Asserter.assert_equals(responses[1].status, httpcode.NOT_FOUND)
    Asserter.assert_equals(responses[2].status, httpcode.SERVICE_UNAVAILABLE)
