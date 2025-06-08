from typing import Dict, List, Tuple
import json

from .text_generator import ITextGenerator
from .app_types import HistoryData
from .database import (
    Problem,
    Solution,
    Review,
    TheoryText,
)
from .constants import Difficulty


class TaskWriter:
    def __init__(
        self,
        text_generator: ITextGenerator,
        system_prompt: str,
        user_prompt: str
    ) -> None:
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.text_generator = text_generator

    def generate(
        self,
        tags: List[TheoryText],
        additional_instructions: str,
        difficulty: Difficulty,
        previous_problems: List[Problem]
    ) -> str:
        history: HistoryData = []
        history.append({
            "role": "system",
            "content": self.system_prompt.format(
                tags=', '.join([tag.name for tag in tags]),
                additional_instructions=additional_instructions,
                difficulty=difficulty.value
            )
        })
        for problem in previous_problems:
            history.append({
                "role": "user",
                "content": problem.name + '\n'
                + problem.task + '\n'
                + 'Сложность задачи: ' + problem.difficulty.value
            })
        history.append({
            "role": "user",
            "content": self.user_prompt
        })
        print('[DEBUG] TaskWriter history:', json.dumps(
            history,
            ensure_ascii=False,
            indent=4
        ))

        return self.text_generator.generate(history)


class TestWriter:
    def __init__(
        self,
        text_generator: ITextGenerator,
        system_prompt: str
    ) -> None:
        self.system_prompt = system_prompt
        self.text_generator = text_generator

    def generate(self, task: str) -> str:
        history: HistoryData = []
        history.append({
            "role": "system",
            "content": self.system_prompt
        })
        history.append({
            "role": "user",
            "content": task
        })
        return self.text_generator.generate(history)


class Reviewer:
    def __init__(
        self,
        text_generator: ITextGenerator,
        system_prompt: str,
    ) -> None:
        self.system_prompt = system_prompt
        self.text_generator = text_generator

    def generate(
        self,
        task: str,
        solutions_history: List[Tuple[Solution, Review]],
        tags: str,
        last_solution_code: str,
        tests: str,
        tests_results: Dict[str, Dict[str, str]]
    ) -> str:
        history: HistoryData = []
        history.append({
            "role": "system",
            "content": self.system_prompt.format(
                task=task,
                tags=tags,
                tests=tests,
                tests_results=json.dumps(
                    tests_results,
                    ensure_ascii=False,
                    indent=4
                )
            )
        })
        for solution, review in solutions_history:
            history.append({
                "role": "user",
                "content": solution.content
            })
            history.append({
                "role": "assistant",
                "content": review.content
            })
        history.append({
                "role": "user",
                "content": last_solution_code
        })

        print('[DEBUG] Reviewer history:', json.dumps(
            history,
            ensure_ascii=False,
            indent=4
        ))
        return self.text_generator.generate(history)


class Adjudicator:
    def __init__(
        self,
        text_generator: ITextGenerator,
        system_prompt: str
    ) -> None:
        self.system_prompt = system_prompt
        self.text_generator = text_generator

    def adjudicate(
        self,
        task: str,
        solution_code: str,
        review: str
    ) -> bool:
        history: HistoryData = []
        history.append({
            "role": "system",
            "content": self.system_prompt.format(
                task=task
            )
        })
        history.append({
            "role": "user",
            "content": solution_code
        })
        history.append({
            "role": "user",
            "content": review
        })

        response = self.text_generator.generate(history)
        return eval(response.strip())
