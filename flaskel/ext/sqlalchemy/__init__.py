from flask_sqlalchemy import SQLAlchemy

from .events import register_engine_events
from .model import SQLAModel
from .support import SQLASupport

db = SQLAlchemy(model_class=SQLAModel)
