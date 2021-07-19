import time

from flaskel.http import HTTPClient


class FetchMail(HTTPClient):
    """
    Fetch emails from sendria
    """

    def __init__(
        self, endpoint, username=None, password=None, retry=3, wait=1, timeout=3
    ):
        """

        :param endpoint:
        :param username:
        :param password:
        :param retry:
        :param wait:
        :param timeout:
        """
        super().__init__(
            endpoint, username=username, password=password, timeout=timeout
        )
        self.retry = retry
        self.wait = wait

    def get(self, recipient, subject=None, **__):
        """

        :param recipient:
        :param subject:
        :return:
        """
        response = []
        resp = self.request("/", raise_on_exc=True)
        for d in resp.body.data:
            if recipient in d.recipients_envelope:
                if subject and d.subject != subject:
                    continue
                response.append(d)

        return response

    def perform(self, recipient=None, subject=None, delete=True):
        """

        :param recipient:
        :param subject:
        :param delete:
        :return:
        """
        for _ in range(0, self.retry):
            res = self.get(recipient, subject)
            if delete:
                for r in res:
                    self.request(uri=f"/{r.id}", method="DELETE")
            if res:
                return res

            time.sleep(self.wait)
            return None
