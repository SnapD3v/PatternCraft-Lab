from flask import g, request
from flask_babel import Babel


def get_locale():
    user = getattr(g, "user", None)
    if user is not None:
        return user.locale

    language = request.accept_languages.best_match(["ru", "en"])
    return language


def get_timezone():
    user = getattr(g, "user", None)
    if user is not None:
        return user.timezone


babel = Babel()
