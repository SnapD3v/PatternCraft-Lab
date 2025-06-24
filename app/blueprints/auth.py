from flask import Blueprint, request, render_template, redirect, url_for, current_app
from app.services import PatternCraftAuthClient
from ..utils import build_nested_update_auto_with_cast
from .. import configure_app
from app.config import AppConfig

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    app_config = current_app.dependencies["app_config"]

    base_url, email, password = (
        app_config.auth.base_url,
        app_config.auth.email,
        app_config.auth.password,
    )

    if request.method == "GET":
        return render_template(
            "login.html", base_url=base_url, email=email, password=password
        )

    base_url = request.form.get("auth.base_url")
    email = request.form.get("auth.email")
    password = request.form.get("auth.password")

    try:
        api_client = current_app.dependencies.get("api_client")
        if (
            isinstance(api_client, PatternCraftAuthClient)
            and api_client.is_authenticated
        ):
            print("=" * 30, "DEBUG", "=" * 30)
            print("Already authenticated")
            return redirect(url_for("profile.profile"))

        # Try to authenticate with provided credentials
        api_client = PatternCraftAuthClient(
            base_url=base_url,
            email=email,
            password=password,
        )

        typed_updates = build_nested_update_auto_with_cast(request.form, AppConfig)
        print(typed_updates)
        app_config = app_config.model_copy(update=typed_updates)

        print("[DEBUG] app_config=", app_config)

        # Обновляем DI
        configure_app(current_app, app_config)

        json_config = app_config.model_dump_json(indent=4, exclude_none=True)
        with open("config.json", "w") as f:
            f.write(json_config)

        current_app.dependencies.update({"api_client": api_client})

        return redirect(url_for("profile.profile"))

    except ConnectionError:
        # flash(
        #     "Could not connect to the PatternCraft service. Please check your URL.",
        #     "error",
        # )
        print("=" * 30, "DEBUG", "=" * 30)
        print("Could not connect to the PatternCraft service. Please check your URL.")
        return (
            render_template(
                "login.html",
                base_url=request.form.get("base_url"),
                email=request.form.get("email"),
            ),
            400,
        )
    # except AuthenticationError:
    #     flash("Invalid login credentials. Please try again.", "error")
    # return render_template(
    #     "login.html",
    #     base_url=request.form.get('base_url'),
    #     email=request.form.get('email')
    # ), 400
    except Exception as e:
        # flash(f"An error occurred: {str(e)}", "error")
        print("=" * 30, "DEBUG", "=" * 30)
        print(f"An error occurred: {str(e)}")
        return (
            render_template(
                "login.html",
                base_url=request.form.get("base_url"),
                email=request.form.get("email"),
            ),
            400,
        )
