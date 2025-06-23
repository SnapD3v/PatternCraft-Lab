from typing import List, Optional, cast

from flask import Blueprint, current_app, jsonify, request, make_response, render_template, redirect

from app.services.auth_service import PatternCraftAuthClient
from app.services.service_adapter import ServiceAdapter

from ..database import Course, TextsBlock, TheoryText, Problem, db
from ..dto import CourseDTO
import base64

courses_bp = Blueprint('courses', __name__)


@courses_bp.route("/courses", methods=["GET"])
def courses_list():
    courses_list = cast(List[Course], Course.query.all())
    return make_response(
        render_template('courses_list.html', courses=courses_list)
    )


@courses_bp.route("/course/<int:course_id>", methods=["GET"])
def course(course_id: int):
    course = CourseDTO(Course.query.get(course_id))
    if not course:
        return make_response("Курс не найден", 404)

    return make_response(
        render_template(
            'course.html',
            course=course
        )
    )


@courses_bp.route("/delete_course", methods=["DELETE"])
def delete_course():
    course_id = int(request.json['course_id'])
    course = cast(Optional[Course], Course.query.get(course_id))
    if not course:
        return jsonify({'error': 'Курс не найден'})
    db.session.delete(course)
    db.session.commit()
    return jsonify({'message': 'Курс успешно удален'})


@courses_bp.route("/course/edit/<int:course_id>", methods=["GET", "POST"])
def edit_course(course_id: int):
    course = cast(Optional[Course], Course.query.get(course_id))
    if not course:
        return make_response("Курс не найден", 404)

    if request.method == 'GET':
        texts_blocks = cast(List[TextsBlock], TextsBlock.query.all())
        problems = cast(List[Problem], Problem.query.all())
        return make_response(
            render_template(
                'course_form.html',
                course=course,
                sections=texts_blocks,
                problems=problems,
                selected_theory_ids=[str(t.id) for t in course.theories],
                selected_problem_ids=[str(p.id) for p in course.problems]
            )
        )

    name = request.form['name']
    description = request.form['description']
    image_url = request.form.get('image_url', '')

    is_hidden = request.form.get('is_hidden') == 'on'
    theory_texts_ids = request.form.get('theory_texts', '').split(',') if request.form.get('theory_texts') else []
    problems_ids = request.form.get('problems', '').split(',') if request.form.get('problems') else []

    course.name = name
    course.description = description
    course.image_url = image_url
    course.is_hidden = is_hidden
    course.theories = TheoryText.query.filter(
        TheoryText.id.in_(theory_texts_ids)
    ).all()
    course.problems = Problem.query.filter(
        Problem.id.in_(problems_ids)
    ).all()

    db.session.add(course)
    db.session.commit()

    if 'image' in request.files and request.files['image']:
        filename = f'app/static/img/courses/{course.id}.png'
        image = request.files['image']
        image.save(filename)
        course.image_url = ''

    db.session.add(course)
    db.session.commit()

    return make_response(redirect(f'/course/{course.id}'))


@courses_bp.route("/course/create", methods=["GET", "POST"])
def create_course():
    if request.method == 'GET':
        texts_blocks = cast(List[TextsBlock], TextsBlock.query.all())
        problems = cast(List[Problem], Problem.query.all())
        return make_response(
            render_template(
                'course_form.html',
                course=None,
                sections=texts_blocks,
                problems=problems,
                selected_theory_ids=[],
                selected_problem_ids=[]
            )
        )

    name = request.form['name']
    description = request.form['description']
    image_url = request.form.get('image_url', '')

    is_hidden = request.form.get('is_hidden') == 'on'
    theory_texts_ids = request.form.get('theory_texts', '').split(',') if request.form.get('theory_texts') else []
    problems_ids = request.form.get('problems', '').split(',') if request.form.get('problems') else []
    course = Course(
        name=name,
        description=description,
        image_url=image_url,
        is_hidden=is_hidden
    )
    course.theories = TheoryText.query.filter(
        TheoryText.id.in_(theory_texts_ids)
    ).all()
    course.problems = Problem.query.filter(
        Problem.id.in_(problems_ids)
    ).all()
    db.session.add(course)
    db.session.commit()
    if 'image' in request.files and request.files['image']:
        filename = f'app/static/img/courses/{course.id}.png'
        image = request.files['image']
        image.save(filename)
        course.image_url = ''
    db.session.add(course)
    db.session.commit()
    id = course.id
    return make_response(redirect(f'/course/{id}'))



@courses_bp.route("/download_course", methods=["GET"])
def download_course():
    course_link = request.args['course_link']
    id = int(course_link.split('/')[-1])  # Получаем ID курса из ссылки
    auth_client: PatternCraftAuthClient = current_app.dependencies["api_client"]
    service_adapter = ServiceAdapter(auth_client=auth_client)
    course = service_adapter.download_course(course_id=id)

    return redirect(f'/course/{course.id}')


@courses_bp.route("/send_course", methods=["POST"])
def send_course():
    course_id = int(request.json["course_id"])
    course = cast(Optional[Course], Course.query.get(course_id))
    if not course:
        return jsonify({"error": "Курс не найден"}), 404

    api_client: PatternCraftAuthClient = current_app.dependencies["api_client"]

    # Get CSRF token from cookies
    csrf_token = api_client.session.cookies.get("csrftoken")

    headers = {"X-CSRFToken": csrf_token}

    for problem in course.problems:
        response = api_client.request(
            "POST",
            "/api/create-task",
            json={
                "name": problem.name,
                "description": problem.task,
                "tests": problem.tests[0].code,
                "tags": problem.tags,
                "difficulty": problem.difficulty.name,
                "language": problem.language.name,
                "author_id": api_client.id,
                "is_hidden": course.is_hidden
            },
            cookies=api_client.session.cookies,
            headers=headers,
        )

        if response.status_code != 201:
            return response.text, response.status_code
        
        json_response = response.json()
        server_problem_id = json_response.get("id")
        problem.server_problem_id = server_problem_id
        db.session.commit()
    
    for theory in course.theories:
        image_data = theory.image_url
        if not theory.image_url:
            filename = f'app/static/img/theory/{theory.id}.png'
            with open(filename, "rb") as image_file:
                image_data = image_file.read()
                image_data = 'data:image/png;base64,' + base64.b64encode(image_data).decode('utf-8')

        response = api_client.request(
            "POST",
            "/api/create-theory",
            json={
                "name": theory.name,
                "description": theory.description,
                "content": theory.content,
                "image": image_data,
                "author_id": api_client.id,
                "is_hidden": course.is_hidden
            },
            cookies=api_client.session.cookies,
            headers=headers,
        )

        if response.status_code != 201:
            return response.text, response.status_code
        
        json_response = response.json()
        server_theory_id = json_response.get("id")
        theory.server_theory_id = server_theory_id
        db.session.commit()

    image_data = course.image_url
    if not course.image_url:
        filename = f'app/static/img/courses/{course.id}.png'
        with open(filename, "rb") as image_file:
            image_data = image_file.read()
            image_data = 'data:image/png;base64,' + base64.b64encode(image_data).decode('utf-8')

    response = api_client.request(
        "POST",
        "/courses/api/create-course",
        json={
            "name": course.name,
            "description": course.description,
            "image": image_data,
            "theories": [theory.server_theory_id for theory in course.theories],
            "problems": [problem.server_problem_id for problem in course.problems],
            "is_hidden": course.is_hidden,
            "author_id": api_client.id
        },
        cookies=api_client.session.cookies,
        headers=headers,
    )

    json_response = response.json()
    print(json_response)
    server_course_id = json_response.get("id")
    course.server_course_id = server_course_id
    db.session.commit()

    return jsonify({"message": "Курс успешно отправлен"})