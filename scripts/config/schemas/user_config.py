"""
Description: User config that contains personal custom settings.
"""

from enum import Enum
from pydantic import BaseModel, SecretStr
from scripts.config.config import settings


class DifficultyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HARD = "hard"


class Theme(str, Enum):
    DARK = "dark"
    LIGHT = "light"


class AppearanceConfig(BaseModel):
    theme: Theme = Theme.DARK
    language: str = settings.defaults.default_language


class EducationConfig(BaseModel):
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM


class APIConfig(BaseModel):
    api_key: SecretStr | None = None
    model: str = settings.defaults.default_model


class UserConfig(BaseModel):
    api: APIConfig

    appearance: AppearanceConfig

    education: EducationConfig
