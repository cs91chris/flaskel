import flask
# Define your forms in this package and import them here


def flash_errors(form, redirect=None):
    for field, errors in form.errors.items():
        for e in errors:
            flask.flash(f"{getattr(form, field).label.text}: {e}")
        if redirect:
            return flask.redirect(flask.url_for(redirect))
