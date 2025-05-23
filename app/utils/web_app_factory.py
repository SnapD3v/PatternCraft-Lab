"""
Description: Factory class for creating and configuring the web application instance
with all necessary routes and settings.
"""

from flask import Flask
from ..views.route_provider import IRouteProvider


class WebAppFactory:
    @staticmethod
    def create_app(routes: IRouteProvider) -> Flask:
        app = Flask(__name__, template_folder="../templates", static_folder="../static")
        routes.register(app)
        return app
