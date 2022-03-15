from flaskel.extra.account import AccountModel as BaseAccountModel
from ..ext import database as db


class AccountModel(db.Model, BaseAccountModel):
    __tablename__ = "accounts"
