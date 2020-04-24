# example spa blueprint
#
from flask import Blueprint, current_app as cap

from flaskel.ext import errors

import os

static_folder = os.environ.get('SPA_STATIC_FOLDER') or 'webapp'
static_url_path = os.environ.get('SPA_STATIC_URL_PATH') or 'static'

spa = Blueprint(
    'spa', __name__,
    static_folder=static_folder,
    static_url_path=static_url_path
)

errors.web_register(spa)


@spa.route('/', defaults={'path': ''})
@spa.route('/<path:path>')
def catch_all(path):
    """

    :param path:
    :return:
    """
    return cap.send_static_file("index.html")
