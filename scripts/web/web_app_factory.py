from flask import Flask
from .route_provider import IRouteProvider


class WebAppFactory:
    @staticmethod
    def create_app(routes: IRouteProvider) -> Flask:
        app = Flask(__name__, template_folder="../../templates", static_folder="../../static")
        routes.register(app)
        return app
