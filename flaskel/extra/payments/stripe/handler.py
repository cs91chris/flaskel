import typing as t

from vbcore.datastruct import ObjectDict
from vbcore.http import httpcode

from flaskel import cap, request, abort

try:
    import stripe
    from stripe.error import StripeError
except ImportError:
    stripe = StripeError = None

CallbackType = t.Callable[[t.Dict[str, t.Any]], t.Any]


class PaymentHandler:
    payment_intent_ok: str = "payment_intent.succeeded"
    payment_intent_ko: str = "payment_intent.payment_failed"

    def __init__(self, app=None, **kwargs):
        self._stripe = stripe
        self._error: CallbackType = self._not_registered
        self._success: CallbackType = self._not_registered

        if app is not None:
            self.init_app(app, **kwargs)

    @staticmethod
    def _not_registered(*_):
        cap.logger.warning("no callback registered")

    def check_prerequisites(self, app):
        assert self._stripe is not None, "you must install 'stripe'"
        assert app.config.STRIPE_SECRET_KEY is not None, "missing STRIPE_SECRET_KEY"
        assert app.config.STRIPE_PUBLIC_KEY is not None, "missing STRIPE_PUBLIC_KEY"

    def init_app(self, app, name: t.Optional[str] = None, **kwargs):
        self.check_prerequisites(app)
        app.config.setdefault("STRIPE_DEBUG", False)
        app.config.setdefault("STRIPE_DEFAULT_CURRENCY", "eur")
        app.config.setdefault("STRIPE_API_VERSION", "2020-08-27")

        self._stripe.api_key = app.config.STRIPE_SECRET_KEY
        self._stripe.api_version = app.config.STRIPE_API_VERSION
        self._stripe.log = "debug" if app.config.STRIPE_DEBUG else "info"
        self._stripe.set_app_info(name or app.config.APP_NAME, **kwargs)

        setattr(app, "extensions", getattr(app, "extensions", {}))
        app.extensions["stripe"] = self

    @staticmethod
    def prepare_amount(value):
        return int(value * 100)

    def create_payment_intent(
        self, amount: t.Union[float, int], currency: t.Optional[str] = None, **kwargs
    ) -> ObjectDict:
        return ObjectDict(
            **self._stripe.PaymentIntent.create(
                amount=self.prepare_amount(amount),
                currency=currency or cap.config.STRIPE_DEFAULT_CURRENCY,
                **kwargs,
            )
        )

    def create_event(self, data: bytes, raise_exc: bool = False) -> ObjectDict:
        webhook_secret = cap.config.STRIPE_WEBHOOK_SECRET
        signature = request.headers.get("stripe-signature")
        try:
            return ObjectDict(
                **self._stripe.Webhook.construct_event(
                    payload=data, sig_header=signature, secret=webhook_secret
                )
            )
        except StripeError as exc:
            cap.logger.exception(exc)
            if not raise_exc:
                return ObjectDict()
            raise

    def webhook_handler(self) -> t.Any:
        data = self.create_event(request.data)
        event_type = data.type
        if event_type == self.payment_intent_ok:
            return self._success(data)
        if event_type == self.payment_intent_ko:
            return self._error(data)

        cap.logger.warning("unhandled event type received: %s\n%s", event_type, data)
        return abort(httpcode.NOT_FOUND)

    def on_success(self, callback: CallbackType) -> CallbackType:
        self._success = callback
        return callback

    def on_error(self, callback: CallbackType) -> CallbackType:
        self._error = callback
        return callback
