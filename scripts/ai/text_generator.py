from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam


class ITextGenerator(ABC):
    @abstractmethod
    def generate(
        self, history: List[ChatCompletionMessageParam], model: Optional[str] = None
    ) -> str:
        pass


class TextGenerator(ITextGenerator):
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        self.model = model

    def generate(
        self, history: List[ChatCompletionMessageParam], model: Optional[str] = None
    ) -> str:
        model = model or self.model
        completion = self.client.chat.completions.create(model=model, messages=history)
        if completion.choices[0].message.content:
            return completion.choices[0].message.content
        raise TypeError
