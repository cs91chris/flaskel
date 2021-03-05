import flask

from flaskel import cap, httpcode, uuid
from . import bp_test


@bp_test.route('/method_override', methods=['POST', 'PUT'])
def method_override_post():
    return '', httpcode.SUCCESS if flask.request.method == 'PUT' else httpcode.METHOD_NOT_ALLOWED


@bp_test.route('/test_https')
def test_https():
    remote = cap.extensions['cloudflareRemote']
    return {
        'address': remote.get_client_ip(),
        'scheme':  flask.request.scheme,
        'url_for': flask.url_for('test.test_https', _external=True)
    }


@bp_test.route('/proxy')
def test_proxy():
    return {
        "request_id":  flask.request.id,
        'script_name': flask.request.environ['SCRIPT_NAME'],
        'original':    flask.request.environ['werkzeug.proxy_fix.orig']
    }


@bp_test.route("/list/<list('-'):data>")
def list_converter(data):
    return flask.jsonify(data)


@bp_test.route('/invalid-json', methods=['POST'])
def get_invalid_json():
    payload = flask.request.json
    return '', httpcode.SUCCESS


@bp_test.route('/download')
def download():
    response = cap.response_class
    return response.send_file('./', flask.request.args.get('filename'))


@bp_test.route('/uuid')
def return_uuid():
    return dict(
        uuid1=uuid.get_uuid(ver=1),
        uuid3=uuid.get_uuid(ver=3),
        uuid4=uuid.get_uuid(),
        uuid5=uuid.get_uuid(ver=5),
    )


@bp_test.route('/crypt/<passwd>')
def crypt(passwd):
    crypto = cap.extensions['argon2']
    return crypto.generate_hash(passwd)


@bp_test.route('/useragent')
def useragent():
    return flask.g.user_agent.to_dict()
