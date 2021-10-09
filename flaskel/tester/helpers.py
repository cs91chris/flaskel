from base64 import b64encode
from functools import partial

import flask

from flaskel import ConfigProxy
from flaskel import httpcode
from flaskel.ext.sqlalchemy.support import SQLASupport
from flaskel.http import HttpMethod
from flaskel.tester import FetchMail
from flaskel.tester.mixins import Asserter

config = ConfigProxy()
schemas = ConfigProxy("SCHEMAS")
url_for = partial(flask.url_for, _external=True)


class CTS:
    text = "text/plain"
    json = "application/json"
    xml = "application/xml"
    html = "text/html"
    json_problem = "application/problem+json"
    xml_problem = "application/problem+xml"
    json_health = "application/health+json"


def load_sample_data(filename):
    SQLASupport.exec_from_file(
        config.SQLALCHEMY_DATABASE_URI, filename, echo=config.SQLALCHEMY_ECHO
    )


def fetch_emails(subject, recipient=None):
    client = FetchMail(config.SENDRIA)
    return client.perform(recipient=recipient, subject=subject)


def basic_auth_header(username=None, password=None):
    username = username or config.BASIC_AUTH_USERNAME
    password = password or config.BASIC_AUTH_PASSWORD
    token = b64encode(f"{username}:{password}".encode()).decode()
    return dict(Authorization=f"Basic {token}")


def build_url(url=None, view=None, params=None, **kwargs):
    params = params or {}
    args = "&".join([f"{k}={v}" for k, v in params.items()])
    if view is not None:
        return f"{url_for(view, **kwargs)}?{args}", args  # noqa F405
    return f"{url}?{args}", args  # noqa F405


def api_tester(
    client,
    url=None,
    view=None,
    schema=None,
    status=httpcode.SUCCESS,
    params=None,
    **kwargs,
):
    kwargs.setdefault("method", HttpMethod.GET)
    url, _ = build_url(url, url_for(view) if view else None, params)
    res = client.open(url, **kwargs)
    Asserter.assert_status_code(res, status)
    if schema:
        Asserter.assert_schema(res.json, schema)
    return res


def post_api_tester(client, **kwargs):
    api_tester(client, method=HttpMethod.POST, **kwargs)


def put_api_tester(client, **kwargs):
    api_tester(client, method=HttpMethod.PUT, **kwargs)


def get_api_tester(client, **kwargs):
    api_tester(client, method=HttpMethod.GET, **kwargs)


def delete_api_tester(client, **kwargs):
    api_tester(client, method=HttpMethod.DELETE, **kwargs)


def patch_api_tester(client, **kwargs):
    api_tester(client, method=HttpMethod.PATCH, **kwargs)


def restful_tester(
    client,
    view,
    headers=None,
    res_id=None,
    body_create=None,
    body_update=None,
    schema_read=None,
    schema_collection=None,
    methods=(HttpMethod.GET, HttpMethod.POST, HttpMethod.PUT, HttpMethod.DELETE),
    **params,
):  # pylint: disable=R0913
    url_collection, args = build_url(view=view, params=params)

    if HttpMethod.POST in methods:
        res = client.post(url_collection, json=body_create, headers=headers)
        Asserter.assert_status_code(res, httpcode.CREATED)
        Asserter.assert_schema(res.json, schema_read)
        res_id = res.json.id

    url_resource = f"{url_for(view, res_id=res_id)}?{args}"
    if HttpMethod.GET in methods:
        res = client.get(url_collection, headers=headers)
        Asserter.assert_status_code(res)
        Asserter.assert_schema(res.json, schema_collection)

        res = client.get(url_resource, headers=headers)
        Asserter.assert_status_code(res)
        Asserter.assert_schema(res.json, schema_read)

    if HttpMethod.PUT in methods:
        body_update = body_update or body_create
        res = client.put(url_resource, headers=headers, json=body_update)
        Asserter.assert_status_code(res)
        Asserter.assert_schema(res.json, schema_read)

    if HttpMethod.DELETE in methods:
        res = client.delete(url_resource, headers=headers)
        Asserter.assert_status_code(res, httpcode.NO_CONTENT)

        res = client.get(url_resource, headers=headers)
        Asserter.assert_status_code(res, httpcode.NOT_FOUND)
        Asserter.assert_schema(res.json, schemas.API_PROBLEM)
