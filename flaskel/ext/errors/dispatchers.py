import flask
from flask import current_app as cap


class ErrorDispatcher:
    @staticmethod
    def default(exc):
        return (
            flask.render_template_string(exc.default_html_template, exc=exc),
            exc.code,
        )

    def dispatch(self, exc, **kwargs):
        raise NotImplementedError


class DefaultDispatcher(ErrorDispatcher):
    def dispatch(self, exc, **kwargs):
        return self.default(exc)


class SubdomainDispatcher(ErrorDispatcher):
    def dispatch(self, exc, **kwargs):
        len_domain = len(cap.config.get("SERVER_NAME") or "")
        if len_domain > 0:
            subdomain = flask.request.host[:-len_domain].rstrip(".") or None
            for bp_name, bp in cap.blueprints.items():
                if subdomain == bp.subdomain:
                    handler = cap.error_handler_spec.get(bp_name, {}).get(exc.code)
                    for v in (handler or {}).values():
                        return v(exc)
        else:  # pragma: no cover
            cap.logger.warning(
                "You must set 'SERVER_NAME' in order to use %s", self.__class__
            )

        return self.default(exc)  # pragma: no cover


class URLPrefixDispatcher(ErrorDispatcher):
    def dispatch(self, exc, **kwargs):
        for bp_name, bp in cap.blueprints.items():
            if not bp.url_prefix:
                cap.logger.warning(
                    "You must set 'url_prefix' when instantiate Blueprint: '%s'",
                    bp_name,
                )
                continue

            if flask.request.path.startswith(bp.url_prefix):
                handler = cap.error_handler_spec.get(bp_name, {}).get(exc.code)
                for v in (handler or {}).values():
                    return v(exc)

        return self.default(exc)  # pragma: no cover


DEFAULT_DISPATCHERS = {
    "default": DefaultDispatcher,
    "subdomain": SubdomainDispatcher,
    "urlprefix": URLPrefixDispatcher,
}
