from typing import List, Optional, cast

from flask import Blueprint, current_app, jsonify, request, make_response, render_template, redirect

from app.services.auth_service import PatternCraftAuthClient
from app.services.service_adapter import ServiceAdapter

from ..database import Course, TextsBlock, TheoryText, Problem, db
from ..dto import CourseDTO

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



@courses_bp.route("/api/courses/<int:id>", methods=["POST"])
def copy_course(id: int):
    auth_client: PatternCraftAuthClient = current_app.dependencies["api_client"]

    course = cast(Optional[Course], Course.query.get(id))

    print(id)

    if not course:
        service_adapter = ServiceAdapter(auth_client=auth_client)
        course = service_adapter.download_course(course_id=id)

    return jsonify({"ok": True})
