from flask_sqlalchemy import SQLAlchemy

from .model import SQLAModel

db = SQLAlchemy(model_class=SQLAModel)
