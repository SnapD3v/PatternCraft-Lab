import requests
from bs4 import BeautifulSoup
from datetime import datetime

AUTH_ERROR_MESSAGE = (
    "\n"
    "\n"
    "#### Error message #########################################################\n"
    "# Login failed... Credentials might be updated in the future with settings #\n"
    "############################################################################\n"
    "\n"
)


class PatternCraftAuthClient:
    """
    PatternCraftAuthClient — HTTP клиент авторизации и работы с PatternCraft API.

    Использование внутри Flask DI:

    1. Инициализация (в configure_app):

        user_client = PatternCraftAuthClient(
            base_url=config.auth.base_url,
            email=config.auth.email,
            password=config.auth.password
        )

        app.dependencies = {
            "api_client": user_client,
            ...
        }

    2. Получение клиента в обработчиках:

        from flask import current_app

        def some_view():
            api_client: PatternCraftAuthClient = current_app.dependencies["api_client"]
            response = api_client.request("GET", "/api/some-endpoint")
            if response.ok:
                data = response.json()
                ...

    3. Особенности:
        - Автоматический логин при первом запросе
        - Повторная авторизация при сбросе сессии
        - RuntimeError при невозможности логина

    4. Требуемая конфигурация:
        config.auth.base_url: str  # Базовый URL PatternCraft (изменить после деплоя)
        config.auth.email: str     # Email пользователя
        config.auth.password: str  # Пароль пользователя
    """

    def __init__(self, base_url, email, password):
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.id = None
        self.username = None
        self.created_at = None
        self.is_authenticated = False

        self.login()

    def _get_csrf_token(self):
        login_page = self.session.get(f"{self.base_url}/login")

        # Update session with all cookies from the login page response
        for cookie in login_page.cookies:
            self.session.cookies.set(
                cookie.name, cookie.value, domain=cookie.domain, path=cookie.path
            )

        soup = BeautifulSoup(login_page.text, "html.parser")
        csrf_input = soup.find("input", {"name": "login-csrf_token"})
        if not csrf_input:
            raise RuntimeError("CSRF token not found on login page")

        csrf_token = csrf_input["value"]

        # Manually set csrftoken cookie if not present
        if "csrftoken" not in login_page.cookies:
            self.session.cookies.set(
                "csrftoken", csrf_token, domain="127.0.0.1", path="/"
            )

        return csrf_input["value"]

    def login(self):
        csrf_token = self._get_csrf_token()

        data = {
            "login-csrf_token": csrf_token,
            "login-identity": self.email,
            "login-password": self.password,
        }

        headers = {"Referer": f"{self.base_url}/login"}

        response = self.session.post(
            f"{self.base_url}/api/login",
            data=data,
            headers=headers
        )
        response_data = response.json()
        user_id = response_data.get("id")
        username = response_data.get("username")
        created_at = response_data.get("created_at")
        if not (user_id and username and created_at):
            print(AUTH_ERROR_MESSAGE)
            self.id = None
            self.username = None
            self.created_at = None
            self.is_authenticated = False
            return

        self.id = user_id
        self.username = username
        self.created_at = datetime.fromisoformat(created_at)
        self.is_authenticated = True

    def request(self, method, path, **kwargs):
        if not self.is_authenticated:
            self.login()
            if not self.is_authenticated:
                raise RuntimeError(
                    "Login failed. Please check your credentials in settings."
                )

        url = f"{self.base_url}{path}"
        response = self.session.request(method, url, **kwargs)

        return response


"""
from flask import Blueprint, current_app, jsonify

example_bp = Blueprint("example", __name__)


@example_bp.route("/example")
def example():
    api_client: PatternCraftAuthClient = current_app.dependencies["api_client"]

    try:
        response = api_client.request("GET", "/api/user/profile")
        response.raise_for_status()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(response.json())
"""
