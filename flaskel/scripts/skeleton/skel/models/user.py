from ext.database import database as db

from flaskel.extra.account import AccountModel as BaseAccountModel


class AccountModel(db.Model, BaseAccountModel):
    __tablename__ = "accounts"
