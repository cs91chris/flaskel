from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr
from vbcore import json
from vbcore.datastruct import IntEnum, ObjectDict
from vbcore.db.mixins import CatalogMixin, StandardMixin
from vbcore.db.sqla import LoaderModel


class PaymentStatusValue(IntEnum):
    WAIT = 1
    SUCCESS = 2
    ERROR = 3


class PaymentStatus(CatalogMixin, LoaderModel):
    __abstract__ = True

    values = PaymentStatusValue.to_list()

    def to_dict(self, **__):
        return ObjectDict(id=self.id, stato=self.label)


class Payment(StandardMixin):
    _status_model = PaymentStatus

    request_id = sa.Column(sa.String(255), unique=True, nullable=False)
    response_id = sa.Column(sa.String(255), unique=True)
    client_id = sa.Column(sa.String(255), nullable=False)

    receipt_url = sa.Column(sa.String(255))
    request = sa.Column(sa.Text)
    response = sa.Column(sa.Text)
    made_on = sa.Column(sa.DateTime)
    canceled_at = sa.Column(sa.DateTime)
    cancellation_reason = sa.Column(sa.Text)
    payment_method = sa.Column(sa.String(255))

    @declared_attr
    def status_id(self):
        return sa.Column(sa.Integer, sa.ForeignKey(self._status_model.id))

    @declared_attr
    def status(self):
        return sa.orm.relationship(
            self._status_model,
            foreign_keys=self.status_id,
            uselist=False,
            lazy="joined",
        )  # type: ignore


class PaymentRepo:
    def __init__(self, session, model):
        self.model = model
        self.session = session

    def save(self, data: ObjectDict, **kwargs):
        try:
            self.session.add(
                self.model(
                    request_id=data.id,
                    request=json.dumps(data),
                    status_id=PaymentStatusValue.WAIT,
                    **kwargs,
                )
            )
            self.session.commit()
        except sa.exc.SQLAlchemyError:
            self.session.rollback()
            raise

    def get_payment(self, request_id: str) -> Payment:
        return self.model.query.filter_by(request_id=request_id).first_or_404()

    def update(self, status: PaymentStatusValue, event: ObjectDict):
        try:
            data = event.data.object.charges.data[0]
        except (AttributeError, IndexError):
            data = ObjectDict()

        payment = self.get_payment(event.data.object.id)
        payment.status_id = status
        payment.response_id = data.id
        payment.made_on = datetime.now()
        payment.response = json.dumps(data)
        payment.receipt_url = data.receipt_url

        try:
            self.session.add(payment)
            self.session.commit()
        except sa.exc.SQLAlchemyError:
            self.session.rollback()
            raise
