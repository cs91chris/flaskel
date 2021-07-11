from base64 import b64encode
from functools import partial

import flask

from flaskel import ConfigProxy, httpcode
from flaskel.ext.sqlalchemy.support import SQLASupport
from flaskel.tester import FetchMail
from flaskel.tester.mixins import Asserter

__all__ = [
    'ConfigProxy', 'httpcode', 'Asserter',
    'config', 'schemas', 'url_for',
    'basic_auth_header', 'restful_tester', 'api_tester',
    'fetch_emails', 'load_sample_data'
]

config = ConfigProxy()
schemas = ConfigProxy('SCHEMAS')
url_for = partial(flask.url_for, _external=True)


def load_sample_data(filename):
    SQLASupport.exec_from_file(
        config.SQLALCHEMY_DATABASE_URI,
        filename,
        echo=config.SQLALCHEMY_ECHO
    )


def fetch_emails(subject, recipient=None):
    client = FetchMail(config.SENDRIA)
    return client.perform(recipient=recipient, subject=subject)


def basic_auth_header(username=None, password=None):
    username = username or config.BASIC_AUTH_USERNAME
    password = password or config.BASIC_AUTH_PASSWORD
    token = b64encode(f"{username}:{password}".encode()).decode()
    return dict(Authorization=f"Basic {token}")


def api_tester(client, url=None, view=None, schema=None, status=httpcode.SUCCESS, **kwargs):
    kwargs.setdefault('method', 'GET')
    res = client.open(url_for(view) if view else url, **kwargs)
    Asserter.assert_status_code(res, status)
    if schema:
        Asserter.assert_schema(res.json, schema)
    return res


def restful_tester(
        client, view, headers=None, res_id=None,
        body_create=None, body_update=None,
        schema_read=None, schema_collection=None,
        methods=('GET', 'POST', 'PUT', 'DELETE'), **params
):
    args = '&'.join([f"{k}={v}" for k, v in params.items()])
    url_collection = f"{url_for(view)}?{args}"

    if 'POST' in methods:
        res = client.post(url_collection, json=body_create, headers=headers)
        Asserter.assert_status_code(res, httpcode.CREATED)
        Asserter.assert_schema(res.json, schema_read)
        res_id = res.json.id

    url_resource = f"{url_for(view, res_id=res_id)}?{args}"
    if 'GET' in methods:
        res = client.get(url_collection, headers=headers)
        Asserter.assert_status_code(res)
        Asserter.assert_schema(res.json, schema_collection)

        res = client.get(url_resource, headers=headers)
        Asserter.assert_status_code(res)
        Asserter.assert_schema(res.json, schema_read)

    if 'PUT' in methods:
        body_update = body_update or body_create
        res = client.put(url_resource, headers=headers, json=body_update)
        Asserter.assert_status_code(res)
        Asserter.assert_schema(res.json, schema_read)

    if 'DELETE' in methods:
        res = client.delete(url_resource, headers=headers)
        Asserter.assert_status_code(res, httpcode.NO_CONTENT)

        res = client.get(url_resource, headers=headers)
        Asserter.assert_status_code(res, httpcode.NOT_FOUND)
        Asserter.assert_schema(res.json, schemas.ApiProblem)
