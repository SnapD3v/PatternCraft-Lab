from flask import Flask
from requests.exceptions import ConnectionError

from .config import AppConfig
from .services import ProblemService
from .extensions import (
    babel,
    get_locale,
    get_timezone,
)
from app import constants
from app.text_generator import APITextGenerator
from app.ai import TaskWriter, TestWriter, Reviewer, Adjudicator
from app.services import (
    ProblemCreator,
    SolutionChecker,
    ProblemService,
    PatternCraftAuthClient,
)
from app.test_runner import TestRunner
from . import constants


def configure_app(app: Flask, config: AppConfig) -> Flask:
    text_generator = APITextGenerator(
        str(config.api.base_url), config.api.key, config.api.model
    )
    task_writer = TaskWriter(
        constants.IDEA_SYSTEM_PROMPT,
        constants.TASK_SYSTEM_PROMPT,
        constants.IDEA_USER_PROMPT,
        constants.TASK_USER_PROMPT,
        text_generator,
    )
    test_writer = TestWriter(
        text_generator, constants.TEST_WRITER_SYSTEM_PROMPT)
    problem_creator = ProblemCreator(task_writer, test_writer)
    test_runner = TestRunner()
    reviewer = Reviewer(text_generator, constants.REVIEWER_PROMPT)
    adjudicator = Adjudicator(
        text_generator, constants.ADJUDICATOR_SYSTEM_PROMPT)
    solution_checker = SolutionChecker(test_runner, reviewer, adjudicator)
    problem_service = ProblemService(problem_creator, solution_checker)
    babel.init_app(
        app,
        locale_selector=get_locale,
        timezone_selector=get_timezone,
        default_translation_directories=config.translations.directory,
    )

    try:
        user_client = PatternCraftAuthClient(
            str(config.auth.base_url), config.auth.email, config.auth.password
        )
    except ConnectionError:
        user_client = None

    app.dependencies = {
        "app_config": config,
        "problem_service": problem_service,
        "text_generator": text_generator,
        "api_client": user_client,
    }

    return app


def register_blueprints(app: Flask) -> Flask:
    # Импортируй блюпринты тут (чтобы не было циклических импортов)
    from app.blueprints.problems import problems_bp
    from app.blueprints.theory import theory_bp
    from app.blueprints.config import config_bp
    from app.blueprints.assistant import assistant_bp
    from app.blueprints.other import other_bp
    from app.blueprints.courses import courses_bp
    from app.blueprints.profile import profile_bp

    # Зарегистрируй блюпринты
    app.register_blueprint(problems_bp)
    app.register_blueprint(theory_bp)
    app.register_blueprint(config_bp)
    app.register_blueprint(assistant_bp)
    app.register_blueprint(other_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(profile_bp)

    return app
