import flask
from flask import Blueprint
from vbcore.http import httpcode

from flaskel import cap

bp_test = Blueprint("test", __name__)


@bp_test.route("/method_override", methods=["POST", "PUT"])
def method_override_post():
    return (
        "",
        httpcode.SUCCESS
        if flask.request.method == "PUT"
        else httpcode.METHOD_NOT_ALLOWED,
    )


@bp_test.route("/test_https")
def test_https():
    remote = cap.extensions["cloudflareRemote"]
    return {
        "address": remote.get_client_ip(),
        "scheme": flask.request.scheme,
        "url_for": flask.url_for("test.test_https", _external=True),
    }


@bp_test.route("/proxy")
def test_proxy():
    return {
        "request_id": flask.request.id,
        "script_name": flask.request.environ["SCRIPT_NAME"],
        "original": flask.request.environ["werkzeug.proxy_fix.orig"],
    }


@bp_test.route("/list/<list('-'):data>")
def list_converter(data):
    return flask.jsonify(data)


@bp_test.route("/invalid-json", methods=["POST"])
def get_invalid_json():
    _ = flask.request.json
    return "", httpcode.SUCCESS


@bp_test.route("/download")
def download():
    response = cap.response_class
    return response.send_file("./", flask.request.args.get("filename"))
