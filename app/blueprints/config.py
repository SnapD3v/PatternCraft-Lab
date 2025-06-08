import json

from flask import Blueprint, current_app, request, render_template, make_response, redirect

from ..config import AppConfig
from ..utils import build_nested_update_auto_with_cast
from .. import configure_app

config_bp = Blueprint('config', __name__)


@config_bp.route("/config", methods=["GET", "POST"])
def configuration():
    app_config: AppConfig = current_app.dependencies['app_config']

    if request.method == 'GET':
        return make_response(render_template('config.html', config=app_config))

    typed_updates = build_nested_update_auto_with_cast(request.form, AppConfig)
    app_config = app_config.model_copy(update=typed_updates)

    print('[DEBUG] app_config=', app_config)

    # Обновляем DI
    configure_app(current_app, app_config)

    json_config = app_config.model_dump_json(indent=4, exclude_none=True)
    with open('config.json', 'w') as f:
        f.write(json_config)
    return make_response(redirect('/config'))