from base64 import b64encode
from functools import partial

import flask

from flaskel import ConfigProxy, httpcode, ObjectDict
from flaskel.tester.fetchmail import FetchMail
from flaskel.tester.mixins import Asserter

SENDRIA_CONFIG = dict(
    endpoint='http://sendria.local:61000/api/messages',
    username='guest123',
    password='guest123'
)

VIEWS = ObjectDict(
    access_token='auth.access_token',
    refresh_token='auth.refresh_token',
    revoke_token='auth.revoke_token',
)

TEST_DATA = ObjectDict(

)

config = ConfigProxy()
schemas = ConfigProxy('SCHEMAS')
url_for = partial(flask.url_for, _external=True)


def basic_auth_header(username=None, password=None):
    username = username or config.BASIC_AUTH_USERNAME
    password = password or config.BASIC_AUTH_PASSWORD
    token = b64encode(f"{username}:{password}".encode()).decode()
    return dict(Authorization=f"Basic {token}")


def fetch_emails(subject, recipient=None):
    client = FetchMail(**SENDRIA_CONFIG)
    return client.perform(recipient=recipient, subject=subject)


def restful_testing(
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
