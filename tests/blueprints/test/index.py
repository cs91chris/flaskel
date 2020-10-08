import flask

from . import test
from flaskel import httpcode, cap
from flaskel.utils import http, uuid


@test.route('/method_override', methods=['POST', 'PUT'])
def method_override_post():
    return '', httpcode.SUCCESS if flask.request.method == 'PUT' else httpcode.METHOD_NOT_ALLOWED


@test.route('/test_https')
def test_https():
    remote = cap.extensions['cloudflareRemote']
    return {
        'address': remote.get_client_ip(),
        'scheme': flask.request.scheme,
        'url_for': flask.url_for('test.test_https', _external=True)
    }


@test.route('/proxy')
def test_proxy():
    return {
        'script_name': flask.request.environ['SCRIPT_NAME'],
        'original': flask.request.environ['werkzeug.proxy_fix.orig']
    }


@test.route("/list/<list('-'):data>")
def list_converter(data):
    return flask.jsonify(data)


@test.route('/invalid-json', methods=['POST'])
def get_invalid_json():
    http.get_json()
    return '', httpcode.SUCCESS


@test.route('/download')
def download():
    return http.send_file('./', flask.request.args.get('filename'))


@test.route('/uuid')
def return_uuid():
    return flask.jsonify(dict(
        uuid1=uuid.get_uuid(ver=1),
        uuid3=uuid.get_uuid(ver=3),
        uuid4=uuid.get_uuid(),
        uuid5=uuid.get_uuid(ver=5),
    ))


@test.route('/crypt/<passwd>')
def crypt(passwd):
    from flask import current_app as cap

    crypto = cap.extensions['argon2']
    return crypto.generate_hash(passwd)


@test.route('/useragent')
def useragent():
    return flask.g.user_agent.to_dict()
