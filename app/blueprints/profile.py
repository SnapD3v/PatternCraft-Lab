from flask import Blueprint, render_template, current_app
from datetime import datetime
from app.services import PatternCraftAuthClient
from ..config import AppConfig

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile", methods=["GET"])
def profile():
    try:
        api_client = current_app.dependencies.get("api_client")

        return render_template(
            "profile.html",
            email=api_client.email,
            username=api_client.username,
            created_at=api_client.created_at
        )
    except Exception as e:
        print(f"Ошибка в профиле: {e}")
        return render_template("profile.html")


@profile_bp.route("/edit", methods=["GET"])
def edit_profile():
    try:
        user_data = {"username": "Имя Пользователя", "email": "user@example.com"}
        return render_template("edit_profile.html", current_user=user_data)
    except Exception as e:
        print(f"Ошибка в редактировании профиля: {e}")
        return render_template("edit_profile.html", current_user={})


@profile_bp.route("/change-password", methods=["GET"])
def change_password():
    return render_template("change_password.html")


@profile_bp.route("/logout")
def logout():
    app_config: AppConfig = current_app.dependencies["app_config"]

    logout_api_client()

    base_url, email, password = (
        app_config.auth.base_url,
        app_config.auth.email,
        app_config.auth.password,
    )

    return render_template(
        "login.html", base_url=base_url, email=email, password=password
    )


def logout_api_client() -> None:
    api_client = current_app.dependencies.get("api_client")
    if isinstance(api_client, PatternCraftAuthClient) and api_client.is_authenticated:
        api_client.is_authenticated = False
