import re


class Case:
    _CHECK_CAMEL_REGEX = re.compile(r"^([a-zA-Z]).([0-9a-zA-Z])*$")
    _CHECK_SNAKE_REGEX = re.compile(r"((^|_+)[a-z0-9]*)*$")
    _CHECK_KEBAB_REGEX = re.compile(r"((^|-+)[a-z0-9]*)*$")
    _CHECK_WORDS_REGEX = re.compile(r"[0-9a-zA-Z\u0020]", re.UNICODE)
    _SUB_CAMEL_REGEX = re.compile(r"((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))")

    @staticmethod
    def is_camel(text: str):
        """

        :param text:
        :return:
        """
        return bool(Case._CHECK_CAMEL_REGEX.match(text))

    @staticmethod
    def is_snake(text: str):
        """

        :param text:
        :return:
        """
        return bool(Case._CHECK_SNAKE_REGEX.match(text))

    @staticmethod
    def is_kebab(text: str):
        """

        :param text:
        :return:
        """
        return bool(Case._CHECK_KEBAB_REGEX.match(text))

    @staticmethod
    def are_words(text: str):
        """

        :param text:
        :return:
        """
        return bool(Case._CHECK_WORDS_REGEX.match(text))

    @staticmethod
    def to_camel(text: str):
        """

        :param text:
        :return:
        """
        tmp = "".join(w for w in text.title() if w.isalnum())
        return tmp[0].lower() + tmp[1:]

    @staticmethod
    def to_snake(text: str):
        """

        :param text:
        :return:
        """
        tmp = Case.to_camel(text)
        return Case._SUB_CAMEL_REGEX.sub(r"_\1", tmp).lower()

    @staticmethod
    def to_kebab(text: str):
        """

        :param text:
        :return:
        """
        return Case.to_snake(text).replace("_", "-")

    @staticmethod
    def to_words(text: str):
        """

        :param text:
        :return:
        """
        return Case.to_snake(text).replace("_", " ")
