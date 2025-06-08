"""
Description: Main entry point of the application
"""

from app.utils.app_runner import AppRunner
from app import create_app

app, settings = create_app()
runner = AppRunner(app, settings.run.model_dump())
runner.run()
