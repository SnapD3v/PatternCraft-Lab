from flask import Blueprint, make_response, render_template

other_bp = Blueprint('other', __name__)


@other_bp.route("/", methods=["GET"])
def index():
    return make_response(
        render_template('index.html')
    )
