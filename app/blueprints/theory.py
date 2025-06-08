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
    if request.method == 'GET':
        return make_response(render_template('theory_form.html', theory=None))
    theory_text = TheoryText(
        name=request.form['name'],
        content=request.form['content'],
        description=request.form['description'],
        image_url=request.form.get('image_url', ''),
        block_id=section_id
    )
    db.session.add(theory_text)
    db.session.commit()
    if 'image' in request.files and request.files['image']:
        filename = f'app/static/img/{theory_text.id}.png'
        image = request.files['image']
        image.save(filename)
        theory_text.image_url = None
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
    texts_block = TextsBlock(name=name, description=description)
    db.session.add(texts_block)
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
        return make_response(render_template('theory_form.html', theory=theory_text))
    for key in request.form:
        value = request.form[key]
        if hasattr(theory_text, key):
            setattr(theory_text, key, value)
    if 'image' in request.files and request.files['image']:
        filename = f'app/static/img/{id}.png'
        image = request.files['image']
        image.save(filename)
        theory_text.image_url = None
    db.session.commit()
    return make_response(redirect(f'/theory/{id}'))