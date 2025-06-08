from typing import Optional

from openai import OpenAI

from ..app_types import HistoryData
from .interface import ITextGenerator


class APITextGenerator(ITextGenerator):
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        self.model = model

    def generate(
        self,
        history: HistoryData,
        model: Optional[str] = None
    ) -> str:
        model = model or self.model
        print('[DEBUG] Model:', model)
        completion = self.client.chat.completions.create(
            model=model,
            messages=history  # type: ignore
        )
        if completion.choices[0].message.content:
            return completion.choices[0].message.content
        raise TypeError
