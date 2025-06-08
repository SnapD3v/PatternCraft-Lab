"""
Description: Defines data transfer objects for problem-related data structures,
providing structured representations for problem information and operations.
"""

import json
import markdown
import app.database as db
from typing import List
from .solution_history_element_dto import SolutionHistoryElementDTO
from ..utils.markdown_utils import strip_markdown


class ProblemDTO:
    def __init__(self, problem: db.Problem) -> None:
        self.id = problem.id
        raw_name = str(problem.name)
        self.name = strip_markdown(raw_name)
        raw_task = str(problem.task)
        self.task = markdown.markdown(raw_task, extensions=["fenced_code", "nl2br"])
        self.tags = self._parse_tags(problem.block.tags_json)
        self.solution_history_elements = [
            SolutionHistoryElementDTO(i) for i in problem.solution_history_elements
        ]

    def _parse_tags(self, tags_json: str) -> List[str]:
        try:
            return json.loads(tags_json)
        except (json.JSONDecodeError, TypeError):
            return []
