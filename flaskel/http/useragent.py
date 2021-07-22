from user_agents import parsers

from flaskel.utils.datastruct import ObjectDict


class UserAgent(parsers.UserAgent):
    def __init__(self, ua_string=None):  # pylint: disable=W0231
        """

        :param ua_string:
        """
        self._parsed = False
        self._cached = None
        self.os = None
        self.device = None
        self.browser = None
        self.ua_string = ua_string

    def parse(self, ua_string=None):
        """

        :param ua_string:
        """
        if ua_string:
            self._cached = None
            self._parsed = False
            self.ua_string = ua_string

        if not self._parsed and self.ua_string:
            parsed = parsers.user_agent_parser.Parse(self.ua_string)
            self.os = parsers.parse_operating_system(**parsed["os"])
            self.browser = parsers.parse_browser(**parsed["user_agent"])
            self.device = parsers.parse_device(**parsed["device"])

        return self.to_dict()

    def to_dict(self):
        """

        :return:
        """
        if self._cached:
            return self._cached  # pragma: no cover

        self._cached = ObjectDict(
            raw=self.ua_string,
            browser=dict(
                family=self.browser.family,
                version=dict(
                    number=self.browser.version, string=self.browser.version_string
                ),
            ),
            os=dict(
                family=self.os.family,
                version=dict(number=self.os.version, string=self.os.version_string),
            ),
            device=dict(
                family=self.device.family,
                brand=self.device.brand,
                model=self.device.model,
                type=dict(
                    mobile=self.is_mobile,
                    tablet=self.is_tablet,
                    pc=self.is_pc,
                    bot=self.is_bot,
                    email_client=self.is_email_client,
                    touch_capable=self.is_touch_capable,
                ),
            ),
        )
        return self._cached
