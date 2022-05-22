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


class ApiTester:
    def __init__(self, client: TestClient, mimetype: t.Optional[str] = None):
        self.client = client
        self.mimetype = mimetype

    def token_header(
        self, call: bool = False, **kwargs
    ) -> t.Union[t.Callable, t.Dict[str, str]]:
        if call is True:
            return get_access_token(self.client, **kwargs)
        return partial(get_access_token, self.client, **kwargs)

    def perform(
        self,
        url: t.Optional[str] = None,
        method: str = HttpMethod.GET,
        view: t.Optional[str] = None,
        schema: t.Optional[str] = None,
        status: t.Optional[int] = None,
        params: t.Optional[dict] = None,
        mimetype: t.Optional[str] = None,
        **kwargs,
    ):
        url, _ = build_url(url_for(view) if view else url, **(params or {}))
        response = self.client.open(url, method=method, **kwargs)

        if status is not None:
            Asserter.assert_status_code(response, status)
        else:
            Asserter.assert_status_code(
                response,
                in_range=True,
                code=(httpcode.SUCCESS - 1, httpcode.MULTIPLE_CHOICES - 1),
            )

        if response.data and (mimetype or self.mimetype):
            Asserter.assert_equals(response.mimetype, mimetype or self.mimetype)

        if schema:
            Asserter.assert_schema(response.json, schema)

        return response

    def post(
        self,
        url: t.Optional[str] = None,
        view: t.Optional[str] = None,
        schema: t.Optional[str] = None,
        status: t.Optional[int] = None,
        params: t.Optional[dict] = None,
        mimetype: t.Optional[str] = None,
        **kwargs,
    ):
        return self.perform(
            method=HttpMethod.POST,
            url=url,
            view=view,
            schema=schema,
            status=status,
            params=params,
            mimetype=mimetype,
            **kwargs,
        )

    def put(
        self,
        url: t.Optional[str] = None,
        view: t.Optional[str] = None,
        schema: t.Optional[str] = None,
        status: t.Optional[int] = None,
        params: t.Optional[dict] = None,
        mimetype: t.Optional[str] = None,
        **kwargs,
    ):
        return self.perform(
            method=HttpMethod.PUT,
            url=url,
            view=view,
            schema=schema,
            status=status,
            params=params,
            mimetype=mimetype,
            **kwargs,
        )

    def get(
        self,
        url: t.Optional[str] = None,
        view: t.Optional[str] = None,
        schema: t.Optional[str] = None,
        status: t.Optional[int] = None,
        params: t.Optional[dict] = None,
        mimetype: t.Optional[str] = None,
        **kwargs,
    ):
        return self.perform(
            method=HttpMethod.GET,
            url=url,
            view=view,
            schema=schema,
            status=status,
            params=params,
            mimetype=mimetype,
            **kwargs,
        )

    def delete(
        self,
        url: t.Optional[str] = None,
        view: t.Optional[str] = None,
        status: t.Optional[int] = None,
        params: t.Optional[dict] = None,
        mimetype: t.Optional[str] = None,
        **kwargs,
    ):
        return self.perform(
            method=HttpMethod.DELETE,
            url=url,
            view=view,
            schema=None,
            status=status,
            params=params,
            mimetype=mimetype,
            **kwargs,
        )

    def patch(
        self,
        url: t.Optional[str] = None,
        view: t.Optional[str] = None,
        schema: t.Optional[str] = None,
        status: t.Optional[int] = None,
        params: t.Optional[dict] = None,
        mimetype: t.Optional[str] = None,
        **kwargs,
    ):
        return self.perform(
            method=HttpMethod.PATCH,
            url=url,
            view=view,
            schema=schema,
            status=status,
            params=params,
            mimetype=mimetype,
            **kwargs,
        )

    def restful(
        self,
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
        url_collection, args = build_url(url_for(view), **params)

        if HttpMethod.POST in methods:
            res = self.post(
                url_collection,
                json=body_create,
                headers=headers,
                status=httpcode.CREATED,
                schema=schema_read,
            )
            res_id = res.json.id

        url_resource = f"{url_for(view, res_id=res_id)}?{args}"

        if HttpMethod.GET in methods:
            self.get(
                url_collection,
                headers=headers,
                schema=schema_collection,
            )
            self.get(
                url_resource,
                headers=headers,
                schema=schema_read,
            )

        if HttpMethod.PUT in methods:
            self.put(
                url_resource,
                headers=headers,
                json=body_update or body_create,
                schema=schema_read,
            )

        if HttpMethod.DELETE in methods:
            self.delete(
                url_resource,
                headers=headers,
                status=httpcode.NO_CONTENT,
            )
            self.get(
                url_resource,
                headers=headers,
                status=httpcode.NOT_FOUND,
                schema=schemas.API_PROBLEM,
            )


def get_access_token(
    client,
    is_query: bool = False,
    token: t.Optional[str] = None,
    token_type: str = "Bearer",
    access_view: str = "auth.token_access",
    credentials: t.Optional[t.Union[t.Dict[str, str], t.Tuple[str, str]]] = None,
) -> t.Dict[str, str]:
    conf = client.application.config

    if token is not None:
        return dict(Authorization=f"{token_type} {token}")

    if not credentials:
        credentials = dict(email=conf.ADMIN_EMAIL, password=conf.ADMIN_PASSWORD)
    elif isinstance(credentials, tuple):
        credentials = dict(email=credentials[0], password=credentials[1])

    tokens = client.post(url_for(access_view), json=credentials)
    if is_query is True:
        return {conf.JWT_QUERY_STRING_NAME: tokens.json.access_token}

    return dict(Authorization=f"{token_type} {tokens.json.access_token}")
