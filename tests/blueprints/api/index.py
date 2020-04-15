from . import api


@api.route('/', methods=['GET'])
def index():
    return {
        "message": "it works!"
    }
