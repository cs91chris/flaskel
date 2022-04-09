from unittest.mock import MagicMock

from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode
from vbcore.http.headers import ContentTypeEnum
from vbcore.tester.mixins import Asserter

from flaskel.ext.default import Database
from flaskel.extra.payments.stripe import (
    PaymentHandler as BasePaymentHandler,
    PaymentIntentView as BasePaymentIntentView,
    PaymentWebhookView as BasePaymentWebhookView,
)
from flaskel.extra.payments.stripe.repo import (
    Payment,
    PaymentStatus as BasePaymentStatus,
)
from flaskel.tester.helpers import ApiTester

db = Database()

CONFIG = ObjectDict(
    STRIPE_SECRET_KEY="STRIPE_SECRET_KEY",
    STRIPE_PUBLIC_KEY="STRIPE_PUBLIC_KEY",
    STRIPE_WEBHOOK_SECRET="STRIPE_WEBHOOK_SECRET",
)

INTENT_ID = "pi_123456"

SAMPLE_INTENT = {
    "id": INTENT_ID,
    "object": "payment_intent",
    "amount": 10000,
    "amount_capturable": 0,
    "amount_received": 0,
    "canceled_at": None,
    "cancellation_reason": None,
    "charges": {
        "object": "list",
        "data": [],
        "has_more": False,
        "url": f"/v1/charges?payment_intent={INTENT_ID}",
    },
    "client_secret": "pi_123_secret_123",
    "confirmation_method": "automatic",
    "created": 1546884062,
    "currency": "eur",
    "invoice": None,
    "metadata": {},
    "payment_method": None,
    "payment_method_options": {},
    "payment_method_types": ["card"],
    "receipt_email": None,
    "shipping": None,
    "status": "requires_payment_method",
}
SAMPLE_WEBHOOK = {
    "api_version": "2020-03-02",
    "created": 1546884065,
    "data": {
        "object": {
            "amount": 10000,
            "amount_capturable": 0,
            "amount_received": 10000,
            "canceled_at": None,
            "cancellation_reason": None,
            "capture_method": "automatic",
            "charges": {
                "data": [
                    {
                        "amount": 10000,
                        "amount_captured": 10000,
                        "amount_refunded": 0,
                        "balance_transaction": "txn_123",
                        "billing_details": {
                            "address": {
                                "city": None,
                                "country": None,
                                "postal_code": None,
                                "state": None,
                            },
                            "email": None,
                            "name": None,
                            "phone": None,
                        },
                        "calculated_statement_descriptor": "COMPANY SPA",
                        "captured": True,
                        "created": 1546884065,
                        "currency": "eur",
                        "fraud_details": {},
                        "id": "ch_123",
                        "invoice": None,
                        "metadata": {},
                        "object": "charge",
                        "outcome": {
                            "network_status": "approved_by_network",
                            "risk_level": "normal",
                            "seller_message": "Payment complete.",
                            "type": "authorized",
                        },
                        "paid": True,
                        "payment_intent": INTENT_ID,
                        "payment_method": "pm_123",
                        "payment_method_details": {
                            "card": {
                                "brand": "mastercard",
                                "checks": {
                                    "address_line1_check": None,
                                    "address_postal_code_check": None,
                                    "cvc_check": "pass",
                                },
                                "country": "IT",
                                "exp_month": 1,
                                "exp_year": 2020,
                                "fingerprint": "AABBCC",
                                "funding": "credit",
                                "last4": "1234",
                                "network": "mastercard",
                                "three_d_secure": {
                                    "authenticated": True,
                                    "authentication_flow": "challenge",
                                    "result": "authenticated",
                                    "succeeded": True,
                                    "version": "1.0.2",
                                },
                            },
                            "type": "card",
                        },
                        "receipt_email": None,
                        "receipt_number": None,
                        "receipt_url": "https://pay.stripe.com/receipts/acct_111/ch_222/rcpt_333",
                        "refunded": False,
                        "refunds": {
                            "data": [],
                            "object": "list",
                            "total_count": 0,
                            "url": "/v1/charges/ch_222/refunds",
                        },
                        "shipping": None,
                        "status": "succeeded",
                    }
                ],
                "object": "list",
                "total_count": 1,
                "url": f"/v1/charges?payment_intent={INTENT_ID}",
            },
            "client_secret": "pi_123_secret_123",
            "confirmation_method": "automatic",
            "created": 1546884065,
            "currency": "eur",
            "id": INTENT_ID,
            "invoice": None,
            "livemode": True,
            "metadata": {},
            "object": "payment_intent",
            "payment_method": "pm_123",
            "payment_method_options": {
                "card": {
                    "installments": None,
                    "network": None,
                    "request_three_d_secure": "automatic",
                }
            },
            "payment_method_types": ["card"],
            "receipt_email": None,
            "shipping": None,
            "status": "succeeded",
        }
    },
    "id": "evt_123",
    "livemode": True,
    "object": "event",
    "pending_webhooks": 1,
    "request": {
        "id": None,
        "idempotency_key": "pi_123-src_123",
    },
    "type": "payment_intent.succeeded",
}


stripe_mock = MagicMock()
stripe_mock.PaymentIntent.create.return_value = SAMPLE_INTENT
stripe_mock.Webhook.construct_event.return_value = SAMPLE_WEBHOOK


class PaymentStatus(db.Model, BasePaymentStatus):
    __tablename__ = "payments_status"


class PaymentModel(db.Model, Payment):
    __tablename__ = "payments"
    _status_model = PaymentStatus


class PaymentHandler(BasePaymentHandler):
    handler = stripe_mock


class PaymentWebhookView(BasePaymentWebhookView):
    model = PaymentModel


class PaymentIntentView(BasePaymentIntentView):
    model = PaymentModel

    def get_client_id(self):
        return 1

    def get_amount(self):
        return 100


EXTENSIONS = {"database": db, "stripe": PaymentHandler()}


def test_payment_intent(testapp):
    app = testapp(
        config=CONFIG,
        extensions=EXTENSIONS,
        views=(PaymentIntentView,),
    )
    client = ApiTester(app.test_client(), mimetype=ContentTypeEnum.JSON)

    response = client.post(view=PaymentIntentView.default_view_name)
    Asserter.assert_equals(response.json, SAMPLE_INTENT)


def test_payment_webhook(testapp):
    app = testapp(
        config=CONFIG,
        extensions=EXTENSIONS,
        views=(PaymentWebhookView,),
    )
    client = ApiTester(app.test_client())

    client.post(
        view=BasePaymentWebhookView.default_view_name,
        status=httpcode.NO_CONTENT,
        data=b"{}",  # yes, json bytes
    )
