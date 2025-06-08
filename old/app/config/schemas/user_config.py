"""
Description: User config that contains personal custom settings.
"""

from enum import Enum
from pydantic import BaseModel, SecretStr
from app.config.config import settings


class DifficultyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HARD = "hard"


class Theme(str, Enum):
    DARK = "dark"
    LIGHT = "light"


class AppearanceConfig(BaseModel):
    theme: Theme = Theme.DARK
    language: str = settings.defaults.language


class EducationConfig(BaseModel):
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM


class OpenrouterClientConfig(BaseModel):
    api_key: SecretStr | None = None
    base_url: str = settings.defaults.base_url


class ModelConfig(BaseModel):
    model_name: str = settings.defaults.model_name  # The name of the openrouter model or the name of the local model on your computer.
    model_type: str = settings.defaults.model_type  # local or online


class LocalModelConfig(BaseModel):
    n_gpu_layers: int = 80  # Offload 80 layers to GPU (matches -ngl 80)
    use_mlock: bool = False  # Avoid memory locking for better performance
    flash_attn: bool = True  # Enable flash attention (matches -fa)
    n_ctx: int = 2048  # Context length (adjust as needed)
    chat_format: str = 'chatml'


class UserConfig(BaseModel):
    model: ModelConfig

    openrouter: OpenrouterClientConfig

    local: LocalModelConfig

    appearance: AppearanceConfig

    education: EducationConfig
