from typing import Type

from flask_sqlalchemy import SQLAlchemy

from .model import SQLAModel

ModelType = Type[SQLAModel]
