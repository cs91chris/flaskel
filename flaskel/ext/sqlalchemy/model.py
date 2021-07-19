from flask_sqlalchemy import Model

from flaskel.utils.datastruct import ObjectDict


class SQLAModel(Model):
    __table__ = None

    def columns(self):
        # noinspection PyUnresolvedReferences
        return self.__table__.columns

    @classmethod
    def get_one(cls, *args, raise_not_found=True, to_dict=True, **kwargs):
        """

        :param raise_not_found:
        :param to_dict:
        :return:
        """
        res = cls.query.filter(*args).filter_by(**kwargs)

        if raise_not_found:
            res = res.first_or_404()
        else:
            res = res.first()
            if res is None:
                return None

        if to_dict is True:
            return res.to_dict()
        return res

    @classmethod
    def query_collection(cls, *args, params=None, **kwargs):  # pylint: disable=W0613
        return cls.query.filter(*args).filter_by(**kwargs)

    @classmethod
    def get_list(
        cls,
        *args,
        to_dict=True,
        restricted=False,
        order_by=None,
        page=None,
        page_size=None,
        max_per_page=None,
        **kwargs,
    ):
        """

        :param to_dict:
        :param restricted:
        :param order_by:
        :param page:
        :param page_size:
        :param max_per_page:
        :return:
        """
        q = cls.query_collection(*args, **kwargs)

        if order_by is not None:
            q = q.order_by(order_by)

        if page or page_size:
            q = q.paginate(page, page_size, False, max_per_page)
            res = q.items
            if to_dict is False:
                return q
        else:
            res = q.all()

        if to_dict is True:
            return [r.to_dict(restricted) for r in res]
        return res

    def update(self, attributes):
        """

        :param attributes:
        :return:
        """
        for attr, val in attributes.items():
            if attr in self.columns():
                setattr(self, attr, val)

        return self

    def to_dict(self, restricted=False):  # pylint: disable=W0613
        """

        :param restricted:
        :return:
        """
        columns = self.columns().keys()
        return ObjectDict(**{col: getattr(self, col, None) for col in columns})
