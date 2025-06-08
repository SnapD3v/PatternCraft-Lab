"""
Description: Implements AI agents for task writing and reviewing. Contains
specialized agents for generating and evaluating programming tasks and solutions.
"""

from typing import Dict, Any, List, Tuple
from abc import ABC, abstractmethod
from .text_generator import ITextGenerator


class Agent(ABC):
    @abstractmethod
    def generate(self, history: List[Dict[str, str]], **kwargs: Dict[str, Any]) -> Any:
        pass


class TaskWriter(Agent):
    def __init__(
        self, text_generator: ITextGenerator, system_prompt: str, user_prompt: str
    ) -> None:
        self.text_generator = text_generator
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt

    def _prepare_history(self, history: List[Dict[str, str]], tags: List[str]) -> None:
        history.insert(0, {"role": "system", "content": self.system_prompt})

        joined_tags = ", ".join(tags)

        history.append(
            {"role": "user", "content": self.user_prompt.format(tags=joined_tags)}
        )

    def generate(
        self, history: List[Dict[str, str]], **kwargs: Dict[str, Any]
    ) -> Tuple[str, str]:
        self._prepare_history(history, tags=kwargs["tags"])
        response = self.text_generator.generate(history)
        name = response.split("\n")[0]
        task = response.lstrip(name).strip()
        return name, task


class Reviewer(Agent):
    def __init__(self, text_generator: ITextGenerator, system_prompt: str) -> None:
        self.text_generator = text_generator
        self.system_prompt = system_prompt

    def _prepare_history(
        self, history: List[Dict[str, str]], tags: List[str], solution: str
    ) -> None:
        joined_tags = ", ".join(tags)

        history.insert(
            0,
            {"role": "system", "content": self.system_prompt.format(tags=joined_tags)},
        )

        history.append({"role": "user", "content": solution})

    def generate(self, history: List[Dict[str, str]], **kwargs: Dict[str, Any]) -> str:
        self._prepare_history(history, tags=kwargs["tags"], solution=kwargs["solution"])
        review = self.text_generator.generate(history)
        return review


class Assistant(Agent):
    def __init__(self, text_generator: ITextGenerator, system_prompt: str) -> None:
        self.text_generator = text_generator
        self.system_prompt = system_prompt

    def _prepare_history(self, history: List[Dict[str, str]], user_prompt: str) -> None:
        history.insert(0, {"role": "system", "content": self.system_prompt})
        history.append({"role": "user", "content": user_prompt})

    def generate(self, history: List[Dict[str, str]], user_prompt: str) -> str:
        self._prepare_history(history, user_prompt)
        response = self.text_generator.generate(history)
        return response
