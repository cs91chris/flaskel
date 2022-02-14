from unittest.mock import patch, MagicMock

from flask import Blueprint
from vbcore.tester.mixins import Asserter
from werkzeug.routing import BaseConverter, FloatConverter

from flaskel import AppBuilder, middlewares, Flaskel, Response
from flaskel.views import BaseView


def get_app() -> Flaskel:
    return Flaskel(__name__)


@patch("flaskel.builder.random_string")
def test_generate_secret_key(mock_random_string, tmpdir):
    secret_str = "secretkey"
    mock_random_string.return_value = secret_str
    file = tmpdir.join("test_generate_secret_key.key")

    builder = AppBuilder(get_app())
    secret_key = builder.generate_secret_key(file.strpath, len(secret_str))
    Asserter.assert_equals(secret_key, secret_str)
    Asserter.assert_equals(file.read(), secret_str)


def test_load_secret_key(tmpdir):
    secret_str = "secretkey"
    file = tmpdir.join("test_load_secret_key.key")
    file.write(secret_str)

    builder = AppBuilder(get_app())
    secret_key = builder.load_secret_key(file.strpath)
    Asserter.assert_equals(secret_key, secret_str)
    Asserter.assert_none(builder.load_secret_key("nofile"))


def test_set_secret_key_dev(caplog):
    app = get_app()
    builder = AppBuilder(app)
    builder.set_config({"FLASK_ENV": "development"})
    builder.set_secret_key()

    Asserter.assert_equals(app.config.JWT_SECRET_KEY, app.config.SECRET_KEY)
    Asserter.assert_equals(app.config.SECRET_KEY, "fake_very_complex_string")
    Asserter.assert_equals(len(caplog.records), 1)
    Asserter.assert_equals(caplog.records[0].levelname, "WARNING")
    Asserter.assert_equals(
        caplog.records[0].getMessage(), "secret key length is less than: 256"
    )


def test_set_secret_key_prod(tmpdir):
    app = get_app()
    builder = AppBuilder(app)
    builder.set_config(
        {
            "FLASK_ENV": "production",
            "JWT_SECRET_KEY": "jwt_secret_key",
        }
    )
    builder.set_secret_key()
    builder.secret_file = tmpdir.join("test_set_secret_key_prod.key")

    Asserter.assert_different(app.config.JWT_SECRET_KEY, app.config.SECRET_KEY)
    Asserter.assert_equals(len(app.config.SECRET_KEY), app.config.SECRET_KEY_MIN_LENGTH)


def test_register_extension(caplog):
    builder = AppBuilder(
        get_app(),
        extensions={
            "invalid": (None, (None,)),
            "ext1": (MagicMock(),),
            "ext2": (MagicMock(), {}),
        },
    )
    builder.set_config({"DEBUG": True})
    builder.register_extensions()

    Asserter.assert_equals(caplog.records[0].levelname, "WARNING")
    Asserter.assert_equals(
        caplog.records[0].getMessage(),
        "Invalid extension 'invalid' configuration '(None, (None,))': "
        "extension could not be None or empty",
    )
    Asserter.assert_equals(caplog.records[1].levelname, "DEBUG")
    Asserter.assert_in("ext1", caplog.records[1].getMessage())
    Asserter.assert_equals(caplog.records[2].levelname, "DEBUG")
    Asserter.assert_in("ext2", caplog.records[2].getMessage())


def test_register_blueprints(caplog):
    builder = AppBuilder(
        get_app(),
        blueprints=(
            Blueprint(import_name="bp1", name="bp1"),
            (Blueprint(import_name="bp2", name="bp2"),),
            (Blueprint(import_name="bp3", name="bp3"), {}),
        ),
    )
    builder.set_config({"DEBUG": True})
    builder.register_blueprints()

    Asserter.assert_equals(len(caplog.records), 3)
    for record in caplog.records:
        Asserter.assert_equals(record.levelname, "DEBUG")
        Asserter.assert_true(record.getMessage().startswith("Registered blueprint"))


def test_register_converters(caplog):
    builder = AppBuilder(
        get_app(),
        converters={
            "conv1": BaseConverter,
            "conv2": FloatConverter,
        },
    )
    builder.set_config({"DEBUG": True})
    builder.register_converters()

    Asserter.assert_equals(len(caplog.records), 12)
    for record in caplog.records:
        Asserter.assert_equals(record.levelname, "DEBUG")
        Asserter.assert_true(record.getMessage().startswith("Registered converter"))


def test_register_template_folders(caplog):
    builder = AppBuilder(
        get_app(),
        folders=(
            "folder1",
            "folder2",
        ),
    )
    builder.set_config({"DEBUG": True})
    builder.register_template_folders()
    Asserter.assert_equals(len(caplog.records), 2)
    for record in caplog.records:
        Asserter.assert_equals(record.levelname, "DEBUG")
        Asserter.assert_true(
            record.getMessage().startswith("Registered template folder")
        )


def test_register_middlewares(caplog):
    builder = AppBuilder(
        get_app(),
        middlewares=(
            middlewares.ForceHttps,
            (middlewares.ForceHttps,),
            (middlewares.ForceHttps, {}),
        ),
    )
    builder.set_config({"DEBUG": True})
    builder.register_middlewares()
    Asserter.assert_equals(len(caplog.records), 3)
    for record in caplog.records:
        Asserter.assert_equals(record.levelname, "DEBUG")
        Asserter.assert_true(record.getMessage().startswith("Registered middleware"))


def test_register_views(caplog):
    class CView(BaseView):
        default_view_name = "cview"

    builder = AppBuilder(
        get_app(),
        views=(
            CView,
            (BaseView,),
            (BaseView, {"name": "view"}),
            (BaseView, Blueprint("testview", "testview"), {"name": "testview"}),
        ),
    )
    builder.set_config({"DEBUG": True})
    builder.register_views()
    Asserter.assert_equals(len(caplog.records), 4)
    for record in caplog.records:
        Asserter.assert_equals(record.levelname, "DEBUG")
        Asserter.assert_true(record.getMessage().startswith("Registered view"))


def test_register_after_request(caplog):
    def after_request_1(resp):
        return resp

    def after_request_2(resp):
        return resp

    builder = AppBuilder(
        get_app(),
        after_request=(
            after_request_1,
            after_request_2,
        ),
    )
    builder.set_config({"DEBUG": True})
    builder.register_after_request()
    Asserter.assert_equals(len(caplog.records), 2)
    for record in caplog.records:
        Asserter.assert_equals(record.levelname, "DEBUG")
        Asserter.assert_true(
            record.getMessage().startswith("Registered function after request")
        )


def test_register_before_request(caplog):
    def before_request_1() -> Response:
        return Response.no_content()

    def before_request_2() -> Response:
        return Response.no_content()

    builder = AppBuilder(
        get_app(),
        before_request=(
            before_request_1,
            before_request_2,
        ),
    )
    builder.set_config({"DEBUG": True})
    builder.register_before_request()
    Asserter.assert_equals(len(caplog.records), 2)
    for record in caplog.records:
        Asserter.assert_equals(record.levelname, "DEBUG")
        Asserter.assert_true(
            record.getMessage().startswith("Registered function before request")
        )


def test_set_linter_and_profiler(caplog):
    builder = AppBuilder(get_app())
    builder.set_config(
        {
            "DEBUG": True,
            "WSGI_WERKZEUG_PROFILER_ENABLED": True,
            "WSGI_WERKZEUG_LINT_ENABLED": True,
        }
    )
    builder.set_linter_and_profiler()
    Asserter.assert_equals(len(caplog.records), 2)
    for record in caplog.records:
        Asserter.assert_equals(record.levelname, "DEBUG")
        Asserter.assert_true(record.getMessage().startswith("Registered"))


def test_dump_urls(caplog):
    builder = AppBuilder(get_app())
    builder.dump_urls()
    Asserter.assert_equals(len(caplog.records), 1)
    Asserter.assert_true(caplog.records[0].getMessage().startswith("Registered routes"))


def test_after_create_hook():
    callback = MagicMock()
    builder = AppBuilder(get_app(), after_create_callback=callback)
    builder.after_create_hook()
    callback.is_called()


def test_create():
    builder = AppBuilder()
    builder.set_secret_key = MagicMock()
    builder.set_config = MagicMock()
    builder.register_extensions = MagicMock()
    builder.register_middlewares = MagicMock()
    builder.register_template_folders = MagicMock()
    builder.register_converters = MagicMock()
    builder.register_views = MagicMock()
    builder.register_blueprints = MagicMock()
    builder.register_after_request = MagicMock()
    builder.register_before_request = MagicMock()
    builder.after_create_hook = MagicMock()

    Asserter.assert_none(builder.app)
    app_config = {"a": 1, "b": 2}
    app = builder.create(app_config)
    Asserter.assert_true(isinstance(app, Flaskel))

    builder.set_secret_key.assert_called_once()
    builder.set_config.assert_called_once_with(app_config)
    builder.register_extensions.assert_called_once()
    builder.register_middlewares.assert_called_once()
    builder.register_template_folders.assert_called_once()
    builder.register_converters.assert_called_once()
    builder.register_views.assert_called_once()
    builder.register_blueprints.assert_called_once()
    builder.register_after_request.assert_called_once()
    builder.register_before_request.assert_called_once()
    builder.after_create_hook.assert_called_once()

    Asserter.assert_true(builder.app)
