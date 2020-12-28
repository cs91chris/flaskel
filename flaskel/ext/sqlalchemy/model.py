from flask_sqlalchemy import Model


class SQLAModel(Model):
    @classmethod
    def get_one(cls, raise_not_found=True, to_dict=True, **kwargs):
        """

        :param raise_not_found:
        :param to_dict:
        :param kwargs:
        :return:
        """
        res = cls.query.filter_by(**kwargs)
        if raise_not_found:
            res = res.first_or_404()
        else:
            res = res.first()
            if res is None:
                return

        if to_dict is True:
            return res.to_dict()
        else:
            return res

    @classmethod
    def get_list(cls, to_dict=True, **kwargs):
        """

        :param to_dict:
        :param kwargs:
        :return:
        """
        res = cls.query.filter_by(**kwargs).all()
        if to_dict is not True:
            return res

        return [r.to_dict() for r in res]
