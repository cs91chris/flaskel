from flask_sqlalchemy import Model, SQLAlchemy


class SQLAModel(Model):
    def get_one(self, **kwargs):
        """

        :param kwargs:
        :return:
        """
        res = self.query.filters(**kwargs).get_or_404()
        return res.to_dict()

    def get_list(self, **kwargs):
        """

        :param kwargs:
        :return:
        """
        res_list = []
        for r in self.query.filters(**kwargs).all():
            res_list.append(r.to_dict())
        return res_list

    def to_dict(self, restricted=False):
        """

        :param restricted:
        """
        raise NotImplemented


db = SQLAlchemy(model_class=SQLAModel)
