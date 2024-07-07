from abc import ABC, abstractmethod

from flask import current_app as cap, request


class BaseWrapper(ABC):
    def __init__(self, data, **opts):
        self.data = data
        self.opts = opts

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return self.dump()

    @abstractmethod
    def dump(self):
        raise NotImplementedError


class LogBuilder:
    wrapper_dump_request = BaseWrapper
    wrapper_dump_response = BaseWrapper

    def __init__(self, get_remote=lambda: None):
        self._get_remote = get_remote

    @abstractmethod
    def request_params(self):
        return {}

    @abstractmethod
    def response_params(self):
        return {}

    def get_remote_address(self):
        return self._get_remote() or request.remote_addr

    @staticmethod
    def level_from_code(code):
        code = int(code / 100)
        if code in (1, 2, 3):
            return cap.logger.info, "SUCCESS"
        if code == 4:
            return cap.logger.warning, "WARNING"
        if code == 5:
            return cap.logger.warning, "ERROR"
        return cap.logger.error, "ERROR"

    def dump_request(self):
        # noinspection PyUnresolvedReferences,PyProtectedMember
        cap.logger.info(
            "%s",
            self.wrapper_dump_request(
                request._get_current_object(),  # pylint: disable=protected-access
                **self.request_params(),
            ),
        )

    def dump_response(self, response):
        log, level = self.level_from_code(response.status_code)
        log(
            "%s",
            self.wrapper_dump_response(
                response,
                level=level,
                **self.response_params(),
            ),
        )
        return response
