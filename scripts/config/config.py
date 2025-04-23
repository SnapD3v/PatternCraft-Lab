from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class RunConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False


class SecretsConfig(BaseModel):
    open_router_api_key: str


class PromptConfig(BaseModel):
    writer_system_prompt: str = (
        'Ты - составитель задач. Твоя цель - придумать небольшую задачу на паттерны проектирования и '
        'принципы программирования, которые указал пользователь. Твоя задача должна быть новой и отличаться '
        'от тех, что прислал пользователь ранее.'
        'Польователь пишет на Python, придумывай задачи только под него'
    )
    writer_user_prompt: str = 'Придумай задачу, решение которой потребует применения: {tags}. Напиши на первой строке название задачи, а после нее подробное ТЗ.'
    reviewer_prompt: str = 'Проверь, правильно ли решена задача. Проверь, соблюдены ли принципы и паттерны: {tags}.'


class TagConfig(BaseModel):
    creational: list[str] = [
        'Factory Method',
        'Abstract Factory',
        'Builder',
        'Prototype',
        'Singleton',
    ]
    structural: list[str] = [
        'Adapter',
        'Bridge',
        'Composite',
        'Decorator',
        'Facade',
        'Flyweight',
        'Proxy',
    ]
    behavioral: list[str] = [
        'Chain of Responsibility',
        'Command',
        'Interpreter',
        'Iterator',
        'Mediator',
        'Memento',
        'Observer',
        'State',
        'Strategy',
        'Template Method',
        'Visitor',
    ]
    solid: list[str] = [
        'SRP',
        'OCP',
        'LSP',
        'ISP',
        'DIP',
    ]

    @property
    def tags_list(self) -> list[str]:
        return [*self.creational,
                *self.structural,
                *self.behavioral,
                *self.solid]


class DefaultsConfig(BaseModel):
    default_model: str = "deepseek/deepseek-r1:free"
    default_language: str = "ru"
    base_url: str = "https://openrouter.ai/api/v1"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="CONFIG__",
        env_file=".env",
    )

    run: RunConfig

    prompt: PromptConfig = PromptConfig()
    tags: TagConfig = TagConfig()

    defaults: DefaultsConfig = DefaultsConfig()


settings = Settings()
