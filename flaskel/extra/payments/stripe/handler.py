import typing as t
from functools import partial

import stripe
from stripe.error import StripeError
from vbcore.datastruct import ObjectDict

from flaskel import cap, request

CallbackType = t.Callable[[t.Dict[str, t.Any]], t.Any]


class PaymentHandler:
    handler = stripe
    payment_intent_ok: str = "payment_intent.succeeded"
    payment_intent_ko: str = "payment_intent.payment_failed"

    def __init__(self, app=None, **kwargs):
        self._error: CallbackType = partial(self._not_registered, "on_error")
        self._success: CallbackType = partial(self._not_registered, "on_success")

        if app is not None:
            self.init_app(app, **kwargs)

    @staticmethod
    def _not_registered(callback_type: str, *_):
        cap.logger.warning("no callback registered for: %s", callback_type)

    @staticmethod
    def check_prerequisites(app):
        assert app.config.STRIPE_SECRET_KEY is not None, "missing STRIPE_SECRET_KEY"
        assert app.config.STRIPE_PUBLIC_KEY is not None, "missing STRIPE_PUBLIC_KEY"

    def init_app(self, app, name: t.Optional[str] = None, **kwargs):
        self.check_prerequisites(app)
        app.config.setdefault("STRIPE_DEBUG", False)
        app.config.setdefault("STRIPE_DEFAULT_CURRENCY", "eur")
        app.config.setdefault("STRIPE_API_VERSION", "2020-08-27")

        self.handler.enable_telemetry = False
        self.handler.api_key = app.config.STRIPE_SECRET_KEY
        self.handler.api_version = app.config.STRIPE_API_VERSION
        self.handler.log = "debug" if app.config.STRIPE_DEBUG else "info"
        self.handler.set_app_info(name or app.config.APP_NAME, **kwargs)

        setattr(app, "extensions", getattr(app, "extensions", {}))
        app.extensions["stripe"] = self

    @staticmethod
    def prepare_amount(value):
        return int(value * 100)

    def create_payment_intent(
        self, amount: t.Union[float, int], currency: t.Optional[str] = None, **kwargs
    ) -> ObjectDict:
        return ObjectDict(
            **self.handler.PaymentIntent.create(
                amount=self.prepare_amount(amount),
                currency=currency or cap.config.STRIPE_DEFAULT_CURRENCY,
                **kwargs,
            )
        )

    def create_event(self, data: bytes, raise_exc: bool = True) -> ObjectDict:
        webhook_secret = cap.config.STRIPE_WEBHOOK_SECRET
        signature = request.headers.get("stripe-signature")
        try:
            return ObjectDict(
                **self.handler.Webhook.construct_event(
                    payload=data, sig_header=signature, secret=webhook_secret
                )
            )
        except StripeError as exc:
            cap.logger.exception(exc)
            if not raise_exc:
                return ObjectDict()
            raise

    def webhook_handler(self) -> t.Tuple[t.Optional[bool], ObjectDict]:
        data = self.create_event(request.data)
        event_type = data.type

        if event_type == self.payment_intent_ok:
            self._success(data)
            return True, data

        if event_type == self.payment_intent_ko:
            self._error(data)
            return True, data

        cap.logger.warning("unhandled event type received: %s\n%s", event_type, data)
        return None, data

    def on_success(self, callback: CallbackType) -> CallbackType:
        self._success = callback
        return callback

    def on_error(self, callback: CallbackType) -> CallbackType:
        self._error = callback
        return callback
