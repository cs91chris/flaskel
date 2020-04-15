from flask import render_template

from . import web


@web.route('/', methods=['GET'], strict_slashes=False)
def index():
    return render_template('index.html')
