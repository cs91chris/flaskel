from flask_sqlalchemy import SQLAlchemy

from .model import SQLAModel
from .support import SQLASupport

db = SQLAlchemy(model_class=SQLAModel)
