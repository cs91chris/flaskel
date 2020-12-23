import importlib

from flask_sqlalchemy import Model, SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import class_mapper
from sqlalchemy_schemadisplay import create_schema_graph, create_uml_graph


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

    def to_dict(self, restricted=False):
        """

        :param restricted:
        """
        return self.__dict__


db = SQLAlchemy(model_class=SQLAModel)


def from_model_to_uml(module):
    """

    :param module:
    :return:
    """
    mappers = []
    models = importlib.import_module(module)

    for attr in dir(models):
        if attr[0] == '_':
            continue
        try:
            cls = getattr(models, attr)
            mappers.append(class_mapper(cls))
        except SQLAlchemyError:
            pass

    return create_uml_graph(
        mappers,
        show_operations=False
    )


def from_db_to_schema(url):
    """

    :param url:
    :return:
    """
    return create_schema_graph(
        metadata=MetaData(url),
        show_datatypes=False,
        show_indexes=False,
        rankdir='LR',
        concentrate=False
    )
