"""
Description: Main entry point of the application. Initializes and configures all
necessary components including text generation, task writing, reviewing, theory
and problems management, and web application setup.
"""

from scripts.config.config import settings
from scripts.config.services.user_config import user_config_manager
import scripts.database as db

from scripts.ai.text_generator import TextGenerator
from scripts.ai.agents import TaskWriter, Reviewer, Assistant
from scripts.content.theory_manager import TheoryManager
from scripts.content.problems_manager import ProblemsManager
from scripts.content.assistant_manager import AssistantManager
from scripts.web.web_routes import WebRoutes
from scripts.web.web_app_factory import WebAppFactory
from scripts.web.app_runner import AppRunner


if __name__ == "__main__":
    user_config = user_config_manager.get_config()
    user_config_manager.print_config()

    text_generator = TextGenerator(
        settings.defaults.base_url,
        user_config.api.api_key.get_secret_value(),
        user_config.api.model,
    )

    task_writer = TaskWriter(
        text_generator,
        settings.prompt.writer_system_prompt,
        settings.prompt.writer_user_prompt,
    )
    reviewer = Reviewer(text_generator, settings.prompt.reviewer_prompt)
    assistant = Assistant(text_generator, settings.prompt.assistant_prompt)

    theory_manager = TheoryManager(db.create_session)
    problems_manager = ProblemsManager(db.create_session, task_writer, reviewer)
    assistant_manager = AssistantManager(db.create_session, assistant)

    routes = WebRoutes(theory_manager, problems_manager, assistant_manager, settings.tags.tags_list)
    app = WebAppFactory.create_app(routes)

    runner = AppRunner(app, settings.run.model_dump())
    runner.run()
