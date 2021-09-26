class HttpMethod:
    POST: str = "POST"
    PUT: str = "PUT"
    GET: str = "GET"
    DELETE: str = "DELETE"
    PATCH: str = "PATCH"
    FETCH: str = "FETCH"
    HEAD: str = "HEAD"
    OPTIONS: str = "OPTIONS"


class WebDavMethod:
    COPY: str = "COPY"
    LOCK: str = "LOCK"
    MKCOL: str = "MKCOL"
    PROPFIND: str = "PROPFIND"
    PROPPATCH: str = "PROPPATCH"
    UNLOCK: str = "UNLOCK"
