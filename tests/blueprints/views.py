from flaskel import ConfigProxy
from flaskel.ext.auth import basic_auth
from flaskel.views.resource import Restful


class ApiItem(Restful):
    post_schema = ConfigProxy("SCHEMAS.ITEM_POST")
    decorators = [basic_auth.login_required]
