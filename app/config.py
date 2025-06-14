from enum import Enum
from pydantic import BaseModel, HttpUrl


class Theme(str, Enum):
    DARK = "dark"
    LIGHT = "light"


class APIConfig(BaseModel):
    base_url: HttpUrl
    key: str
    model: str


class AppearanceConfig(BaseModel):
    theme: Theme
    language: str


class ServerConfig(BaseModel):
    host: str
    port: int
    debug: bool = False


class AuthConfig(BaseModel):
    email: str
    password: str
    base_url: HttpUrl


class AppConfig(BaseModel):
    api: APIConfig
    appearance: AppearanceConfig
    server: ServerConfig
    auth: AuthConfig
