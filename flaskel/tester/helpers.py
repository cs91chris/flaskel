import typing as t
from functools import partial

import flask
from vbcore.db.support import SQLASupport
from vbcore.http import httpcode, HttpMethod
from vbcore.tester.helpers import build_url
from vbcore.tester.mixins import Asserter

from flaskel import TestClient
from flaskel.utils.datastruct import ConfigProxy

config = ConfigProxy()
schemas = ConfigProxy("SCHEMAS")
url_for = partial(flask.url_for, _external=True)


def load_sample_data(filename: str):
    SQLASupport.exec_from_file(
        config.SQLALCHEMY_DATABASE_URI, filename, echo=config.SQLALCHEMY_ECHO
    )


def api_tester(
    client: TestClient,
    url: t.Optional[str] = None,
    view: t.Optional[str] = None,
    schema: t.Optional[str] = None,
    status: int = httpcode.SUCCESS,
    params: t.Optional[dict] = None,
    **kwargs,
):
    kwargs.setdefault("method", HttpMethod.GET)
    url, _ = build_url(url_for(view) if view else url, **(params or {}))
    response = client.open(url, **kwargs)
    Asserter.assert_status_code(response, status)
    if schema:
        Asserter.assert_schema(response.json, schema)
    return response


def post_api_tester(
    client: TestClient,
    url: t.Optional[str] = None,
    view: t.Optional[str] = None,
    schema: t.Optional[str] = None,
    status: int = httpcode.SUCCESS,
    params: t.Optional[dict] = None,
    **kwargs,
):
    return api_tester(
        client,
        method=HttpMethod.POST,
        url=url,
        view=view,
        schema=schema,
        status=status,
        params=params,
        **kwargs,
    )


def put_api_tester(
    client: TestClient,
    url: t.Optional[str] = None,
    view: t.Optional[str] = None,
    schema: t.Optional[str] = None,
    status: int = httpcode.SUCCESS,
    params: t.Optional[dict] = None,
    **kwargs,
):
    return api_tester(
        client,
        method=HttpMethod.PUT,
        url=url,
        view=view,
        schema=schema,
        status=status,
        params=params,
        **kwargs,
    )


def get_api_tester(
    client: TestClient,
    url: t.Optional[str] = None,
    view: t.Optional[str] = None,
    schema: t.Optional[str] = None,
    status: int = httpcode.SUCCESS,
    params: t.Optional[dict] = None,
    **kwargs,
):
    return api_tester(
        client,
        method=HttpMethod.GET,
        url=url,
        view=view,
        schema=schema,
        status=status,
        params=params,
        **kwargs,
    )


def delete_api_tester(
    client: TestClient,
    url: t.Optional[str] = None,
    view: t.Optional[str] = None,
    schema: t.Optional[str] = None,
    status: int = httpcode.SUCCESS,
    params: t.Optional[dict] = None,
    **kwargs,
):
    return api_tester(
        client,
        method=HttpMethod.DELETE,
        url=url,
        view=view,
        schema=schema,
        status=status,
        params=params,
        **kwargs,
    )


def patch_api_tester(
    client: TestClient,
    url: t.Optional[str] = None,
    view: t.Optional[str] = None,
    schema: t.Optional[str] = None,
    status: int = httpcode.SUCCESS,
    params: t.Optional[dict] = None,
    **kwargs,
):
    return api_tester(
        client,
        method=HttpMethod.PATCH,
        url=url,
        view=view,
        schema=schema,
        status=status,
        params=params,
        **kwargs,
    )


def restful_tester(
    client: TestClient,
    view: str,
    res_id=None,
    headers: t.Optional[dict] = None,
    body_create: t.Optional[dict] = None,
    body_update: t.Optional[dict] = None,
    schema_read=None,
    schema_collection=None,
    methods: t.Tuple[str, ...] = (
        HttpMethod.GET,
        HttpMethod.POST,
        HttpMethod.PUT,
        HttpMethod.DELETE,
    ),
    **params,
):
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
