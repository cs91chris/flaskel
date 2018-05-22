from flask_json import as_json

from blueprints.api import api


@api.route('/', methods=['GET'])
@as_json
def index():
    return {
        "message": "it works!"
    }
