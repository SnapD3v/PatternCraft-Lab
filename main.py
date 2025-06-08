from flask import Flask
from flask_migrate import Migrate

from app.config import AppConfig
from app.database import db
from app import configure_app, register_blueprints

config = AppConfig.parse_file('config.json')  # type: ignore

migrate = Migrate()

flask_app = Flask(__name__, static_folder='app/static', template_folder='app/templates')
flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализируем базу данных с приложением
db.init_app(flask_app)
migrate.init_app(flask_app, db)

with flask_app.app_context():
    db.create_all()

app = configure_app(flask_app, config)
app = register_blueprints(app)
app.states = {'task_generating': False}

if __name__ == '__main__':
    server_config = config.server.model_dump()
    app.run(
        host=server_config['host'],
        port=server_config['port'],
        debug=server_config['debug']
    )
