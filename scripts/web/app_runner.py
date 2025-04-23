from typing import Dict, Any
from flask import Flask


class AppRunner:
    def __init__(self, app: Flask, config: Dict[str, Any]) -> None:
        self.app = app
        self.config = config

    def run(self) -> None:
        self.app.run(**self.config)
