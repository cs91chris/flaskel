from vbcore.http import HttpMethod, httpcode

from flaskel import request, ExtProxy, abort, cap
from flaskel.views import BaseView, UrlRule
from .repo import PaymentStatus, PaymentRepo, Payment


class PaymentEndpoint:
    intent = "payment_intent"
    webhook = "payment_webhook"


class PaymentView(BaseView):
    gateway = ExtProxy("stripe")
    repo = PaymentRepo(ExtProxy("sqlalchemy.db.session"), Payment)

    default_view_name = "payments"
    default_urls = (
        UrlRule(url="/stripe/payment/intent", endpoint=PaymentEndpoint.intent),
        UrlRule(url="/stripe/payment/webhook", endpoint=PaymentEndpoint.webhook),
    )
    methods = [
        HttpMethod.POST,
    ]

    def dispatch_request(self, *_, **__):
        if request.endpoint.endswith(PaymentEndpoint.intent):
            return self.payment_intent(request.json, client_id=self.get_client_id())
        if request.endpoint.endswith(PaymentEndpoint.webhook):
            return self.payment_webhook(request.data)

        return abort(
            httpcode.BAD_REQUEST, "no action associated with the requested url"
        )

    def get_client_id(self):
        """must be implemented in subclass"""
        return self.not_implemented()

    def payment_intent(self, data, **kwargs):
        intent = self.gateway.create_payment_intent(data.amount)
        self.repo.save(intent, **kwargs)
        return intent

    def payment_webhook(self, data):
        event = self.gateway.create_event(data)
        if not event:
            abort(httpcode.BAD_REQUEST, response="unable to decode event")

        event_type = event.get("type")
        if event_type == self.gateway.payment_intent_ok:
            status = PaymentStatus.SUCCESSO
        elif event_type == self.gateway.payment_intent_ko:
            status = PaymentStatus.ERRORE
        else:
            cap.logger.warning("unhandled event type received: %s", event_type)
            return

        self.repo.update(status, event)
