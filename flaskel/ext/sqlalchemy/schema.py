import importlib

from sqlalchemy import MetaData, create_mock_engine  # type: ignore
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import class_mapper
from sqlalchemy_schemadisplay import create_schema_graph, create_uml_graph

from flaskel.utils.misc import import_from_module


def model_to_uml(module):
    """

    :param module:
    :return:
    """
    mappers = []
    models = importlib.import_module(module)

    for attr in dir(models):
        if attr[0] == "_":
            continue
        try:
            cls = getattr(models, attr)
            mappers.append(class_mapper(cls))
        except SQLAlchemyError:
            pass

    return create_uml_graph(mappers, show_operations=False)


def db_to_schema(url):
    """

    :param url:
    :return:
    """
    return create_schema_graph(
        metadata=MetaData(url),
        show_datatypes=False,
        show_indexes=False,
        rankdir="LR",
        concentrate=False,
    )


DIALECTS = ["sqlite", "mysql", "oracle", "postgresql", "mssql"]


def dump_model_ddl(dialect: str, metadata: str):
    """

    :param dialect:
    :param metadata:
    """
    dialect = dialect or "sqlite"
    _metadata = import_from_module(metadata)
    engine = create_mock_engine(
        f"{dialect}://",
        executor=lambda sql, *_, **__: print(
            str(sql.compile(dialect=engine.dialect)).replace("\n\n", ";")  # type: ignore
        ),
    )
    _metadata.create_all(engine)
