import argon2 as _argon2
from argon2.exceptions import Argon2Error
from argon2.exceptions import InvalidHash


class Argon2:
    def __init__(self, app=None):
        """

        :param app:
        """
        self.ph = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """

        :param app:
        """
        app.config.setdefault("ARGON2_ENCODING", "utf-8")
        app.config.setdefault("ARGON2_TIME_COST", _argon2.DEFAULT_TIME_COST)
        app.config.setdefault("ARGON2_HASH_LENGTH", _argon2.DEFAULT_HASH_LENGTH)
        app.config.setdefault("ARGON2_MEMORY_COST", _argon2.DEFAULT_MEMORY_COST)
        app.config.setdefault("ARGON2_PARALLELISM", _argon2.DEFAULT_PARALLELISM)
        app.config.setdefault("ARGON2_RANDOM_SALT_LENGTH", _argon2.DEFAULT_RANDOM_SALT_LENGTH)

        self.ph = _argon2.PasswordHasher(
            encoding=app.config['ARGON2_ENCODING'],
            time_cost=app.config['ARGON2_TIME_COST'],
            hash_len=app.config['ARGON2_HASH_LENGTH'],
            memory_cost=app.config['ARGON2_MEMORY_COST'],
            parallelism=app.config['ARGON2_PARALLELISM'],
            salt_len=app.config['ARGON2_RANDOM_SALT_LENGTH']
        )

        if not hasattr(app, 'extensions'):
            app.extensions = dict()
        app.extensions['argon2'] = self

    def generate_hash(self, password):
        """

        :param password:
        :return:
        """
        if not password:
            raise ValueError('password must be not empty')
        return self.ph.hash(password)

    def verify_hash(self, pw_hash, password, exc=False):
        """

        :param pw_hash:
        :param password:
        :param exc:
        :return:
        """
        if exc is False:
            try:
                return self.ph.verify(pw_hash, password)
            except (Argon2Error, InvalidHash):
                return False
        else:
            return self.ph.verify(pw_hash, password)


argon2 = Argon2()
