"""
Description: Manages the creation, retrieval, and organization of programming
problems and their solutions. Handles problem sets and individual problem
operations.
"""

from typing import Dict, Any, List
import json
import app.database as db
from .content_manager import ContentManager
from ..ai.agents import Agent
from ..dto.problem_dto import ProblemDTO
from ..utils.markdown_utils import strip_markdown


class ProblemsManager(ContentManager):
    def __init__(
        self,
        session_factory: db.sessionmaker[db.Session],
        task_writer: Agent,
        reviewer: Agent,
    ) -> None:
        self.session_factory = session_factory
        self.task_writer = task_writer
        self.reviewer = reviewer

    def get_problems_set(self, tags: List[str]) -> int:
        session = self.session_factory()
        tags_json = json.dumps(tags)
        problems_set = (
            session.query(db.ProblemsSet)
            .filter(db.ProblemsSet.tags_json == tags_json)
            .first()
        )
        if problems_set:
            return problems_set.id

        problems_set = db.ProblemsSet(tags_json=tags_json)
        session.add(problems_set)
        session.commit()
        result = problems_set.id

        session.close()
        return result

    def create_problem(self, tags: List[str]) -> int:
        session = self.session_factory()
        problems_set_id = self.get_problems_set(tags)
        problems_set = (
            session.query(db.ProblemsSet)
            .filter(db.ProblemsSet.id == problems_set_id)
            .first()
        )
        existing_problems = problems_set.problems
        history: List[Dict[str, str]] = []
        for problem in existing_problems:
            history_line = {"role": "user", "content": strip_markdown(problem.task)}
            history.append(history_line)
        name, task = self.task_writer.generate(history, tags=tags)
        problem = db.Problem(name=name, task=task)
        problems_set.problems.append(problem)
        session.commit()

        result = problem.id

        session.close()
        return result

    def review_solution(self, problem_id: int, solution: str) -> str:
        session = self.session_factory()
        problem = session.query(db.Problem).filter(db.Problem.id == problem_id).first()
        history: List[Dict[str, str]] = [{"role": "assistant", "content": strip_markdown(problem.task)}]
        for solution_history_element in problem.solution_history_elements:
            role = "assitant" if solution_history_element.id % 2 == 0 else "user"
            history_line = {"role": role, "content": strip_markdown(solution_history_element.content)}
            history.append(history_line)

        tags = json.loads(problem.block.tags_json)

        review = self.reviewer.generate(history, tags=tags, solution=solution)

        solution_history_element = db.SolutionHistoryElement(
            content=solution, type="code"
        )
        problem.solution_history_elements.append(solution_history_element)

        solution_history_element = db.SolutionHistoryElement(
            content=review, type="text"
        )
        problem.solution_history_elements.append(solution_history_element)
        session.commit()
        session.close()

        return review

    def get_problems(self) -> List[ProblemDTO]:
        session = self.session_factory()
        problems = (
            session.query(db.Problem)
            .options(
                db.joinedload(db.Problem.block),
                db.joinedload(db.Problem.solution_history_elements),
            )
            .all()
        )
        session.close()
        return [ProblemDTO(problem) for problem in problems]

    def get_problem(self, id: int) -> ProblemDTO:
        session = self.session_factory()
        problem = (
            session.query(db.Problem)
            .filter(db.Problem.id == id)
            .options(
                db.joinedload(db.Problem.block),
                db.joinedload(db.Problem.solution_history_elements),
            )
            .first()
        )
        session.close()
        return ProblemDTO(problem)

    def delete_problem(self, id: int):
        session = self.session_factory()
        problem = session.query(db.Problem).filter(db.Problem.id == id).first()
        if problem:
            session.delete(problem)
            session.commit()
        session.close()
