from flask import Blueprint, render_template
from datetime import datetime

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

@profile_bp.route('/', methods=['GET'])
def profile():
    try:
        user_data = {
            'username': 'Имя Пользователя',
            'email': 'user@example.com',
            'created_at': datetime(2025, 1, 15)
        }
        return render_template('profile.html', current_user=user_data)
    except Exception as e:
        print(f"Ошибка в профиле: {e}")
        return render_template('profile.html', current_user={})

@profile_bp.route('/edit', methods=['GET'])
def edit_profile():
    try:
        user_data = {
            'username': 'Имя Пользователя',
            'email': 'user@example.com'
        }
        return render_template('edit_profile.html', current_user=user_data)
    except Exception as e:
        print(f"Ошибка в редактировании профиля: {e}")
        return render_template('edit_profile.html', current_user={})

@profile_bp.route('/change-password', methods=['GET'])
def change_password():
    return render_template('change_password.html')