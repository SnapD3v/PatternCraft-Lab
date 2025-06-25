from flask_babel import Babel
from flask import current_app, request


def get_locale():
    # 1. Язык из query-параметра (например, ?lang=ru)
    lang = request.args.get("lang")
    if lang in ["ru", "en"]:
        return lang

    # 2. Язык из конфига (appearance.language)
    app_config = current_app.dependencies.get("app_config")
    if app_config:
        lang = getattr(app_config.appearance, "language", None)
        if lang in ["ru", "en"]:
            return lang

    # 3. Язык браузера
    return request.accept_languages.best_match(["ru", "en"])


def get_timezone():
    user = getattr(g, "user", None)
    if user is not None:
        return user.timezone


babel = Babel()