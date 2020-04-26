class BaseApplication:
    def __init__(self, app, options=None):
        """

        :param app:
        :param options:
        """
        self.application = app
        self.options = options or {}

    def run(self):
        """

        :return:
        """
        raise NotImplemented


class WSGIBuiltin(BaseApplication):
    def run(self):
        """

        :return:
        """
        self.application.run(
            host=self.application.config['APP_HOST'],
            port=self.application.config['APP_PORT'],
            debug=self.application.config['DEBUG']
        )
