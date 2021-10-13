from flaskel.tester import helpers as h


def test_app_runs(test_client):
    h.api_tester(test_client, "/", status=h.httpcode.NOT_FOUND)


def test_cors_headers(test_client):
    headers = test_client.application.config.CORS_EXPOSE_HEADERS
    res = h.api_tester(test_client, url="/", status=h.httpcode.NOT_FOUND)
    h.Asserter.assert_header(res, "Access-Control-Allow-Origin", "*")
    h.Asserter.assert_allin(
        res.headers["Access-Control-Expose-Headers"].split(", "), headers
    )


def test_apidoc(test_client, views):
    headers = h.basic_auth_header()
    res = test_client.get(h.url_for(views.apidocs), headers=headers)
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_content_type(res, h.CTS.html)

    res = test_client.get(h.url_for(views.api_spec), headers=headers)
    h.Asserter.assert_status_code(res)
    h.Asserter.assert_different(res.json, {})
    h.Asserter.assert_content_type(res, h.CTS.json)
