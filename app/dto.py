from typing import List
import json

from .utils import markdown_process, strip_markdown
from .database import (
    Problem,
    Solution,
    Review,
    Course
)


class ReviewDTO:
    def __init__(self, review: Review) -> None:
        self.id = review.id
        self.content = markdown_process(review.content)
        self.tests_results = json.loads(review.tests_results)
        self.is_solved = review.is_solved
        self.solution_id = review.solution_id


class SolutionDTO:
    def __init__(self, solution: Solution) -> None:
        self.id = solution.id
        self.content = solution.content
        self.review = ReviewDTO(solution.review) if solution.review else None


class ProblemDTO:
    def __init__(self, problem: Problem) -> None:
        self.id = problem.id
        self.name = problem.name
        self.task = markdown_process(problem.task)
        self.tags = self._parse_tags(problem.tags)
        self.difficulty = problem.difficulty.value
        self.solutions = problem.solutions
        self.tests_code = problem.tests[0].code
        self.is_solved = problem.is_solved

    def _parse_tags(self, tags: str) -> List[str]:
        return tags.split(', ')


class CourseDTO:
    def __init__(self, course: Course) -> None:
        self.id = course.id
        self.name = course.name
        self.description = course.description
        self.image_url = course.image_url
        self.is_hidden = course.is_hidden
        self.theories = course.theories
        self.problems = [ProblemDTO(problem) for problem in course.problems]