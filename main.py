from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
import multiprocessing as mp
import webview

from app.config import AppConfig
from app.database import db
from app import configure_app, register_blueprints, PatternCraftAuthClient


def run_server(server_config: dict, app_config: AppConfig, ready_event: mp.Event) -> None:
    migrate = Migrate()

    flask_app = Flask(__name__, static_folder="app/static",
                      template_folder="app/templates")
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    CORS(
        flask_app,
        supports_credentials=True,
        origins=["http://127.0.0.1:5000", "http://localhost:5000"],
    )

    # Инициализируем базу данных с приложением
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)

    with flask_app.app_context():
        db.create_all()

    app = configure_app(flask_app, app_config)
    app = register_blueprints(app)
    app.states = {"task_generating": False}

    @app.context_processor
    def inject_app_config():
        api_client: PatternCraftAuthClient = app.dependencies.get("api_client")
        is_authenticated = api_client.is_authenticated if api_client else False
        return dict(
            config=app.dependencies["app_config"], is_authenticated=is_authenticated
        )

    ready_event.set()

    app.run(
        host=server_config["host"],
        port=server_config["port"],
        debug=server_config["debug"],
    )


if __name__ == "__main__":
    mp.freeze_support()
    mp.set_start_method('spawn', force=True)

    app_config = AppConfig.parse_file("config.json")  # type: ignore
    server_config = app_config.server.model_dump()
    server_url = f'http://{server_config['host']}:{server_config['port']}'

    # Запуск в режиме инференса
    if not server_config["debug"]:
        backend_ready = mp.Event()
        # Запускаем сервер в фоновом процессе
        server_process = mp.Process(target=run_server, kwargs={
                                    "server_config": server_config, "app_config": app_config, "ready_event": backend_ready})
        server_process.daemon = True
        server_process.start()

        # Ожидаем, пока сервер не станет доступен
        backend_ready.wait()
        # Создаем окно с веб-контентом
        webview.create_window(title='PatternCraft Lab',
                              url=server_url, fullscreen=True)
        webview.start()

    # Запуск в режиме дебага
    else:
        run_server(server_config, app_config)
