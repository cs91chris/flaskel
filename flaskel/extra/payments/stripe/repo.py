from datetime import datetime

import sqlalchemy as sa
from vbcore import json
from vbcore.datastruct import IntEnum, ObjectDict
from vbcore.db.mixins import CatalogMixin, StandardMixin
from vbcore.db.sqla import LoaderModel


class PaymentStatusValue(IntEnum):
    ATTESA = 1
    SUCCESSO = 2
    ERRORE = 3


class PaymentStatus(CatalogMixin, LoaderModel):
    __tablename__ = "payment_status"

    values = PaymentStatusValue.to_list()

    def to_dict(self, **__):
        return ObjectDict(id=self.id, stato=self.label)


class Payment(StandardMixin):
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

    status_id = sa.Column(sa.Enum(PaymentStatus), sa.ForeignKey("payment_status.id"))
    status = sa.orm.relationship(
        PaymentStatus, foreign_keys=status_id, uselist=False, lazy="joined"
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
                    status_id=PaymentStatus.ATTESA,
                    **kwargs,
                )
            )
            self.session.commit()
        except sa.exc.SQLAlchemyError:
            self.session.rollback()
            raise

    def get_payment(self, request_id: str) -> Payment:
        return self.model.query.get_or_404(request_id)

    def update(self, status: PaymentStatus, event: ObjectDict):
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
