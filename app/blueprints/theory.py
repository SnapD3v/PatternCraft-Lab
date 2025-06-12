from flask import Blueprint, request, make_response, render_template, redirect
from typing import List, cast
from app.database import TextsBlock, TheoryText, db


theory_bp = Blueprint('theory', __name__)


@theory_bp.route("/theory", methods=["GET"])
def theory_list():
    theory_list = cast(List[TextsBlock], TextsBlock.query.all())
    return make_response(
        render_template('theory_list.html', theory=theory_list)
    )


@theory_bp.route("/theory/create/<int:section_id>", methods=["GET", "POST"])
def create_theory(section_id: int):
    section = TextsBlock.query.get(section_id)
    if request.method == 'GET':
        return make_response(
            render_template(
                'theory_form.html',
                theory=None,
                section_in_practice=section.in_practice
            )
        )
    theory_text = TheoryText(
        name=request.form['name'],
        content=request.form['content'],
        description=request.form['description'],
        image_url=request.form.get('image_url', ''),
        in_practice=request.form.get('in_practice') == 'on',
        block_id=section_id
    )
    db.session.add(theory_text)
    db.session.commit()
    if 'image' in request.files and request.files['image']:
        filename = f'app/static/img/theory/{theory_text.id}.png'
        image = request.files['image']
        image.save(filename)
        theory_text.image_url = ''
    db.session.add(theory_text)
    db.session.commit()
    id = theory_text.id
    return make_response(redirect(f'/theory/{id}'))


@theory_bp.route('/section/create', methods=["GET", "POST"])
def create_section():
    if request.method == 'GET':
        return make_response(render_template('section_form.html', section=None))
    name = request.form['name']
    description = request.form['description']
    in_practice = request.form.get('in_practice') == 'on'
    texts_block = TextsBlock(name=name, description=description, in_practice=in_practice)
    db.session.add(texts_block)
    db.session.commit()
    return make_response(redirect('/theory'))


@theory_bp.route("/section/edit/<int:id>", methods=["GET", "POST"])
def edit_section(id: int):
    section = TextsBlock.query.get(id)
    print(section)
    if request.method == 'GET':
        return make_response(render_template('section_form.html', section=section))
    name = request.form['name']
    description = request.form['description']
    print(request.form)
    in_practice = request.form.get('in_practice') == 'on'
    section.name = name
    section.description = description
    section.in_practice = in_practice
    db.session.commit()
    return make_response(redirect('/theory'))


@theory_bp.route("/theory/<int:id>", methods=["GET", "POST"])
def theory(id: int):
    theory = TheoryText.query.get(id)
    return make_response(render_template('theory.html', theory=theory))


@theory_bp.route("/theory/edit/<int:id>", methods=["GET", "POST"])
def edit_theory(id: int):
    theory_text = TheoryText.query.get(id)
    if request.method == 'GET':
        return make_response(
            render_template(
                'theory_form.html',
                theory=theory_text,
                section_in_practice=theory_text.block.in_practice
            )
        )
    theory_text.name = request.form['name']
    theory_text.description = request.form['description']
    theory_text.content = request.form['content']
    theory_text.in_practice = request.form.get('in_practice') == 'on'
    theory_text.image_url = request.form.get('image_url', '')
    if 'image' in request.files and request.files['image']:
        filename = f'app/static/img/theory/{id}.png'
        image = request.files['image']
        image.save(filename)
        theory_text.image_url = ''
    db.session.commit()
    return make_response(redirect(f'/theory/{id}'))