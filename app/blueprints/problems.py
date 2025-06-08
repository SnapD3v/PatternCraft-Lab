from typing import List, Optional, cast
import json

from flask import (
    Blueprint,
    current_app,
    request,
    jsonify,
    make_response,
    render_template
)

from app.database import db, Problem, Solution, Review, Test, TheoryText, TextsBlock
from app.dto import ProblemDTO, SolutionDTO
from app.services import ProblemService
from ..constants import Difficulty

problems_bp = Blueprint('problems', __name__)


@problems_bp.route("/problems", methods=["GET"])
def problems():
    task_generating: bool = current_app.states['task_generating']
    problems = cast(List[Problem], Problem.query.all())
    return make_response(
        render_template(
            'problems.html',
            problems=[ProblemDTO(problem) for problem in problems],
            task_generating=task_generating
        )
    )


@problems_bp.route("/problem/create", methods=["GET"])
def create_problem():
    task_generating: bool = current_app.states['task_generating']
    sections = cast(List[TextsBlock], TextsBlock.query.all())
    return make_response(
        render_template(
            'problem_form.html',
            sections=sections,
            task_generating=task_generating
        )
    )


@problems_bp.route("/create_problem", methods=["POST"])
def create_new_problem():
    task_generating: bool = current_app.states['task_generating']
    if task_generating:
        return jsonify({'message': 'Задача уже создается, подождите'})
    current_app.states['task_generating'] = True
    problem_service: ProblemService = current_app.dependencies['problem_service']
    request_data = request.get_json()
    tags_str: List[str] = request_data['selected_tags']
    tags_str.sort()
    tags: List[TheoryText] = TheoryText.query.filter(
        TheoryText.name.in_(tags_str)
    ).all()
    additional_instructions = request.json.get('additional_instructions', '')
    difficulty_str = request.json.get('difficulty', 'EASY')
    difficulty = Difficulty(difficulty_str)
    str_tags = ', '.join([tag.name for tag in tags])
    previous_problems = cast(List[Problem], Problem.query.filter_by(tags=str_tags).all())
    name, task, tests_code = problem_service.create_problem(
        tags,
        additional_instructions,
        difficulty,
        previous_problems
    )
    problem = Problem(
        name=name,
        task=task,
        tags=str_tags,
        difficulty=difficulty
    )
    test = Test(code=tests_code)
    problem.tests.append(test)
    db.session.add(problem)
    db.session.commit()
    current_app.states['task_generating'] = False
    return jsonify({'message': 'Задача создана'})


@problems_bp.route("/problem/<int:id>", methods=["GET"])
@problems_bp.route("/problem/<int:id>/<int:solution_number>", methods=["GET"])
def problem(id: int, solution_number: int = None):
    problem = cast(Optional[Problem], Problem.query.get(id))
    if not solution_number:
        solution_number = len(problem.solutions) if problem.solutions else 1
    if solution_number <= len(problem.solutions):
        solution = SolutionDTO(problem.solutions[solution_number - 1])
    else:
        solution = None
    return make_response(
        render_template('problem.html',
                        problem=ProblemDTO(problem),
                        solutions_count=len(problem.solutions),
                        solution_number=solution_number,
                        solution=solution)
    )


@problems_bp.route("/delete_problem", methods=["DELETE"])
def delete_problem():
    problem_id = int(request.json['problem_id'])
    problem = cast(Optional[Problem], Problem.query.get(problem_id))
    if not problem:
        return jsonify({'error': 'Задача не найдена'})
    db.session.delete(problem)
    db.session.commit()
    return jsonify({'message': 'Задача успешно удалена'})


@problems_bp.route("/check_solution", methods=["POST"])
def check_solution():
    problem_service: ProblemService = current_app.dependencies['problem_service']
    request_data = request.get_json()
    problem_id = int(request_data['problem_id'])
    problem = cast(Optional[Problem], Problem.query.get(problem_id))
    solution_code = request_data['solution_code']
    solution = Solution(content=solution_code)
    tests_results, review_text, is_solved = problem_service.review_solution(
        problem,
        solution
    )
    review = Review(
        content=review_text,
        solution=solution,
        tests_results=json.dumps(
            tests_results,
            ensure_ascii=False,
            indent=4
        ),
        is_solved=is_solved
    )
    solution.review = review
    problem.solutions.append(solution)
    problem.is_solved = is_solved
    db.session.add(solution)
    db.session.add(review)
    db.session.add(problem)
    db.session.commit()
    return jsonify({'tests_results': tests_results, 'review': review.content, 'is_solved': is_solved})


@problems_bp.route("/change_tests", methods=["POST"])
def change_tests():
    problem_id = int(request.json['problem_id'])
    problem = cast(Optional[Problem], Problem.query.get(problem_id))
    tests_code = request.json['tests_code']
    if not tests_code:
        return jsonify({'error': 'Тесты не могут быть пустыми'})
    if not problem:
        return jsonify({'error': 'Задача не найдена'})
    test = Test(code=tests_code)
    problem.tests = [test]
    db.session.add(test)
    db.session.add(problem)
    db.session.commit()
    return jsonify({'message': 'Тесты успешно обновлены'})


@problems_bp.route("/test_solution", methods=["POST"])
def test_solution():
    problem_service: ProblemService = current_app.dependencies['problem_service']
    problem_id = int(request.json['problem_id'])
    problem = cast(Optional[Problem], Problem.query.get(problem_id))
    solution_code = request.json['solution_code']
    tests_results = problem_service.test_solution(problem, solution_code)
    return jsonify({'tests_results': tests_results})