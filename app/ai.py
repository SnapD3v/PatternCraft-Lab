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
from app.utils import strip_markdown


class TaskWriter:
    def __init__(
        self,
        idea_system_prompt: str,
        task_system_prompt: str,
        idea_user_prompt: str,
        task_user_prompt: str,
        text_generator: ITextGenerator,
    ) -> None:
        self.idea_system_prompt = idea_system_prompt
        self.task_system_prompt = task_system_prompt
        self.idea_user_prompt = idea_user_prompt
        self.task_user_prompt = task_user_prompt
        self.text_generator = text_generator

    def generate(
        self,
        tags: List[TheoryText],
        additional_instructions: str,
        difficulty: Difficulty,
        previous_problems: List[Problem]
    ) -> str:
        idea_history: HistoryData = []

        idea_history.append({
            "role": "system",
            "content": self.idea_system_prompt,
        })

        idea_history.append({
            "role": "user",
            "content": self.idea_user_prompt.format(
                tags=', '.join([tag.name for tag in tags]),
                ideas='; '.join(
                    [problem.name for problem in previous_problems]),
            )
        })

        idea = self.text_generator.generate(idea_history)

        if not idea:
            raise ValueError('Name generation is failed!')

        print('[DEBUG] Idea history:', json.dumps(
            idea_history,
            ensure_ascii=False,
            indent=4
        ))

        task = self.text_generator.generate([
            {
                "role": "system",
                "content": self.task_system_prompt,
            },
            {
                "role": "user",
                "content": self.task_user_prompt.format(
                    idea=idea,
                    additional_instructions=additional_instructions,
                    difficulty=difficulty.value
                ),
            }])

        if not task:
            raise ValueError('Task generation is failed!')

        return idea, task


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
            "content": strip_markdown(task)
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
                task=strip_markdown(task),
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
                task=strip_markdown(task)
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
