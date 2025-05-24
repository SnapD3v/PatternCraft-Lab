"""
Description: Main entry point of the application. Initializes and configures all
necessary components including text generation, task writing, reviewing, theory
and problems management, and web application setup.
"""

from app.config.config import settings
from app.config.services.user_config import user_config_manager
import app.database as db

from app.ai.text_generator import TextGenerator
from app.ai.agents import TaskWriter, Reviewer, Assistant
from app.content.theory_manager import TheoryManager
from app.content.problems_manager import ProblemsManager
from app.content.assistant_manager import AssistantManager
from app.views.web_routes import WebRoutes
from app.utils.web_app_factory import WebAppFactory
from app.utils.app_runner import AppRunner


if __name__ == "__main__":
    user_config = user_config_manager.get_config()
    user_config_manager.print_config()

    text_generator = TextGenerator(
        user_config.model.model_name,
        user_config.model.model_type,
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
