"""
Description: User config manager that loads and manages application settings.
"""

import logging
from pathlib import Path
from pydantic import SecretStr, ValidationError
from scripts.utils.exceptions import (
    TokenNotProvidedException,
    ModelNotProvidedException,
)
from ..schemas.user_config import (
    ModelConfig,
    OpenrouterClientConfig,
    LocalModelConfig,
    AppearanceConfig,
    DifficultyLevel,
    EducationConfig,
    Theme,
    UserConfig,
)
import json
from scripts.utils.logger import setup_logger

from scripts.config.config import settings

logging_level = logging.DEBUG if settings.run.debug else logging.INFO
logger = setup_logger(name=__name__, log_file=None, level=logging_level)


class UserConfigManager:
    CONFIG_FILE = Path("config.json")

    def __init__(self):
        self.config: UserConfig = self._load_config()
        self._validate_config()

    def _validate_config(self):
        if (
            self.config.model.model_type == "online"
            and not self.config.openrouter.api_key
        ):
            raise TokenNotProvidedException

        local_models = Path(__file__).parent.parent.parent.parent / "local_models"
        print(local_models.absolute())
        if self.config.model.model_type == "local" and not any(
            local_models.rglob(self.config.model.model_name)
        ):
            raise ModelNotProvidedException

    def _write_json(self, cfg: UserConfig):
        data = cfg.model_dump()
        secret = cfg.openrouter.api_key
        data["openrouter"]["api_key"] = secret.get_secret_value() if secret else None

        text = json.dumps(data, indent=4, ensure_ascii=False)
        self.CONFIG_FILE.write_text(text, encoding="utf-8")

    def _save_to_json(self):
        try:
            self._write_json(self.config)
        except OSError as e:
            raise OSError(f"Не удалось сохранить конфигурацию: {e}")

    def _load_config(self) -> UserConfig:
        if not self.CONFIG_FILE.is_file():
            default_cfg = UserConfig(
                model=ModelConfig(),
                local=LocalModelConfig(),
                openrouter=OpenrouterClientConfig(),
                appearance=AppearanceConfig(),
                education=EducationConfig(),
            )
            try:
                self.CONFIG_FILE.write_text(
                    default_cfg.model_dump_json(indent=4), encoding="utf-8"
                )
            except OSError as e:
                raise OSError(f"Не удалось создать файл конфигурации: {e}")
            return default_cfg

        try:
            raw = self.CONFIG_FILE.read_text(encoding="utf-8")
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка при разборе JSON ({self.CONFIG_FILE.name}): {e}")

        try:

            return UserConfig.model_validate(data)
        except ValidationError as e:
            raise ValueError(f"Неверный формат конфигурации: {e}")

    def get_config(self) -> UserConfig:
        return self.config

    def update_theme(self, theme: Theme | str):
        self.config.appearance.theme = Theme(theme) if isinstance(theme, str) else theme
        self._save_to_json()

    def update_language(self, language: str):
        self.config.appearance.language = language
        self._save_to_json()

    def update_difficulty(self, level: DifficultyLevel | str):
        self.config.education.difficulty = (
            DifficultyLevel(level) if isinstance(level, str) else level
        )
        self._save_to_json()

    def set_api_key(self, api_key: str):
        self.config.openrouter.api_key = SecretStr(api_key)
        self._save_to_json()

    def print_config(self):
        logger.debug(
            "\n\n\n======== Using User Config ========\n\n%s\n\n===============================\n\n\n",
            self.config.model_dump_json(indent=2),
        )


user_config_manager: UserConfigManager = UserConfigManager()
