import pytest
from vbcore.tester.mixins import Asserter

from flaskel import WSGIFactory
from flaskel.wsgi import DEFAULT_WSGI_SERVERS, WSGIBuiltin


def test_import_ok():
    factory = WSGIFactory(classes=DEFAULT_WSGI_SERVERS)
    wsgi_class = factory.get_class("builtin")
    Asserter.assert_equals(wsgi_class, WSGIBuiltin)


def test_import_error():
    factory = WSGIFactory(
        classes={
            "invalid": "module.not.found:Class",
        }
    )

    with pytest.raises(ImportError) as error:
        factory.get_class("invalid")

    Asserter.assert_equals(str(error.value), "missing 'invalid' dependency")
