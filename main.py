from typing import cast, Dict, Any
import multiprocessing as mp

from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS

from app.config import AppConfig
from app.database import db
from app import configure_app, register_blueprints, PatternCraftAuthClient

from flask_babel import _

if __name__ == "__main__":
    print(_('config_title'))
    mp.set_start_method('spawn', force=True)

config = AppConfig.parse_file("config.json")  # type: ignore

migrate = Migrate()

flask_app = Flask(__name__, static_folder="app/static", template_folder="app/templates")
flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

CORS(
    flask_app,
    supports_credentials=True,
    origins=["http://127.0.0.1:5000", "http://localhost:5000"],
)

db.init_app(flask_app)
migrate.init_app(flask_app, db)

with flask_app.app_context():
    db.create_all()

app = configure_app(flask_app, config)
app = register_blueprints(app)
app.states = {"task_generating": False}  # type: ignore


@app.context_processor
def inject_app_config() -> Dict[str, Any]:
    api_client = cast(PatternCraftAuthClient, app.dependencies.get("api_client"))  # type: ignore
    is_authenticated = api_client.is_authenticated if api_client else False
    return dict(
        config=app.dependencies["app_config"], is_authenticated=is_authenticated  # type: ignore
    )


if __name__ == "__main__":
    server_config = config.server.model_dump()
    app.run(
        host=server_config["host"],
        port=server_config["port"],
        debug=server_config["debug"],
    )