from vbcore.http import HttpMethod

from flaskel import db_session, ExtProxy, Response
from flaskel.views import BaseView

from .repo import Payment, PaymentRepo


class PaymentView(BaseView):
    model = Payment
    repo_class = PaymentRepo
    methods = [HttpMethod.POST]
    gateway = ExtProxy("stripe")

    def __init__(self, session=None):
        self.repo = self.repo_class(session or db_session, self.model)


class PaymentIntentView(PaymentView):
    default_view_name = "payment_intent"
    default_urls = ("/stripe/payment/intent",)

    def dispatch_request(self, *_, **__):
        intent = self.gateway.create_payment_intent(self.get_amount())
        self.repo.save(intent, client_id=self.get_client_id())
        return intent

    def get_amount(self):
        """must be implemented in subclass"""
        return self.not_implemented()

    def get_client_id(self):
        """must be implemented in subclass"""
        return self.not_implemented()


class PaymentWebhookView(PaymentView):
    default_view_name = "payment_webhook"
    default_urls = ("/stripe/payment/webhook",)

    def dispatch_request(self, *_, **__):
        status, event = self.gateway.webhook_handler()
        if status is not None:
            self.repo.update(status, event)

        return Response.no_content()
