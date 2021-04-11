import flask

from flaskel import cap, httpcode

try:
    import stripe
    from stripe.error import StripeError
except ImportError:
    stripe = StripeError = None


class PaymentHandler:
    payment_intent_ok = 'payment_intent.succeeded'
    payment_intent_ko = 'payment_intent.payment_failed'

    def __init__(self, app=None, **kwargs):
        self._stripe = stripe
        self._success = self._not_registered
        self._error = self._not_registered

        if app is not None:
            self.init_app(app, **kwargs)

    @staticmethod
    def _not_registered(*args, **kwargs):
        cap.logger.warning('no callback registered')

    def init_app(self, app, name=None, **kwargs):
        assert self._stripe is not None, "you must install 'stripe'"
        assert app.config.STRIPE_SECRET_KEY is not None, 'missing STRIPE_SECRET_KEY'
        assert app.config.STRIPE_PUBLIC_KEY is not None, 'missing STRIPE_PUBLIC_KEY'

        app.config.setdefault('STRIPE_API_VERSION', '2020-08-27')
        app.config.setdefault('STRIPE_DEFAULT_CURRENCY', 'eur')
        self._stripe.log = 'debug' if app.debug else 'info'
        self._stripe.api_key = app.config.STRIP_SECRET_KEY
        self._stripe.api_version = app.config.STRIPE_API_VERSION
        self._stripe.set_app_info(name or app.config.APP_NAME, **kwargs)

    def create_payment_intent(self, amount, currency=None, **kwargs):
        return self._stripe.PaymentIntent.create(
            amount=amount, currency=currency or cap.config.STRIPE_DEFAULT_CURRENCY, **kwargs
        )

    def create_event(self, data, raise_exc=False):
        webhook_secret = cap.config.STRIPE_WEBHOOK_SECRET
        signature = flask.request.headers.get('stripe-signature')
        if webhook_secret and signature:
            try:
                event = self._stripe.Webhook.construct_event(
                    payload=data, sig_header=signature,
                    secret=cap.config.STRIPE_WEBHOOK_SECRET
                )
                return event['type'], event['data']
            except StripeError as exc:
                cap.logger.exception(exc)
                if raise_exc:
                    raise

        return None, None

    def webhook_handler(self):
        event_type, data = self.create_event(flask.request.json)
        if event_type == self.payment_intent_ok:
            return self._success(data)
        elif event_type == self.payment_intent_ko:
            return self._error(data)
        flask.abort(httpcode.NOT_FOUND)

    def on_success(self, callback):
        self._success = callback
        return callback

    def on_error(self, callback):
        self._error = callback
        return callback
