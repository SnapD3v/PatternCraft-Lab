from typing import Dict, List, Tuple
from ..test_runner import TestRunner
from ..ai import TaskWriter, TestWriter, Reviewer, Adjudicator
from ..database import (
    Problem,
    Solution,
    Review,
    TheoryText
)
from ..constants import Difficulty


class ProblemCreator:
    def __init__(
        self,
        task_writer: TaskWriter,
        test_writer: TestWriter
    ) -> None:
        self.task_writer = task_writer
        self.test_writer = test_writer

    def create_problem(
        self,
        tags: List[TheoryText],
        additional_instructions: str = '',
        difficulty: Difficulty = Difficulty.EASY,
        previous_problems: List[Problem] = []
    ) -> Tuple[str, str, str]:
        name, task = self.task_writer.generate(
            tags,
            additional_instructions,
            difficulty,
            previous_problems
        )

        tests_code = self.test_writer.generate(task)
        tests_code = tests_code.strip('```').replace('python', '')

        return name, task, tests_code


class SolutionChecker:
    def __init__(
        self,
        test_runner: TestRunner,
        reviewer: Reviewer,
        adjidicator: Adjudicator
    ) -> None:
        self.test_runner = test_runner
        self.reviewer = reviewer
        self.adjudicator = adjidicator

    def _parse_solutions(
        self,
        solutions: List[Solution]
    ) -> List[Tuple[Solution, Review]]:
        parsed_solutions: List[Tuple[Solution, Review]] = []
        for solution in solutions:
            review = solution.review
            parsed_solutions.append((solution, review))
        return parsed_solutions

    def review_solution(
        self,
        problem: Problem,
        solution_code: str,
        tests_code: str
    ) -> Tuple[Dict[str, Dict[str, str]], str, bool]:
        tests_result = self.test_runner.run_tests(
            solution_code,
            tests_code
        )
        solutions_history = self._parse_solutions(
            problem.solutions
        )
        review = self.reviewer.generate(
            problem.task,
            solutions_history,
            problem.tags,
            solution_code,
            tests_code,
            tests_result
        )

        tests_status = all(
            i['status'] == 'passed' for i in tests_result.values()
        )

        if not tests_status:
            decision = False
        else:
            decision = self.adjudicator.adjudicate(
                problem.task,
                solution_code,
                review
            )

        return (tests_result, review, decision)


class ProblemService:
    def __init__(
        self,
        problem_creator: ProblemCreator,
        solution_checker: SolutionChecker
    ) -> None:
        self.problem_creator = problem_creator
        self.solution_checker = solution_checker

    def test_solution(
        self,
        problem: Problem,
        solution_code: str
    ) -> Dict[str, Dict[str, str]]:
        tests_code = problem.tests[0].code
        print('[DEBUG] Testing solution:', solution_code)
        print('[DEBUG] Using tests:', tests_code)
        return self.solution_checker.test_runner.run_tests(
            solution_code,
            tests_code
        )

    def create_problem(
        self,
        tags: List[TheoryText],
        additional_instructions: str = '',
        difficulty: Difficulty = Difficulty.EASY,
        previous_problems: List[Problem] = []
    ) -> Tuple[str, str, str]:
        print('[DEBUG]', tags, additional_instructions)
        print('[DEBUG]', *[i.name for i in previous_problems])

        return self.problem_creator.create_problem(
            tags,
            additional_instructions,
            difficulty,
            previous_problems
        )

    def review_solution(
        self,
        problem: Problem,
        solution: Solution
    ) -> Tuple[Dict[str, Dict[str, str]], str, bool]:
        return self.solution_checker.review_solution(
            problem,
            solution.content,
            problem.tests[0].code
        )
