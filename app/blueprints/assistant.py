from flask import Blueprint, current_app, jsonify, request
import json

from typing import List, Dict, Union, cast
from delta import html

from app.database import Chat, Message, db
from ..app_types import ChatsList, HistoryData
from ..utils import markdown_process


assistant_bp = Blueprint('assistant', __name__, url_prefix='/assistant')


@assistant_bp.route("/chats", methods=["GET"])
def chats():
    chats: ChatsList = []
    db_chats = cast(List[Chat], Chat.query.all())
    for chat in db_chats:
        chats.append({
           'id': chat.id,
           'name': chat.name,
        })
    return jsonify({
        'chats': chats
    })


@assistant_bp.route("/chats/create", methods=["POST"])
def create_chat():
    request_data = request.get_json()
    name = request_data.get('name', 'New Chat')
    chat = Chat(name=name)
    context = Message(
        role='context',
        content='Тут будет весь необходимый контекст для чата',
    )
    chat.messages.append(context)
    db.session.add(chat)
    db.session.commit()
    response_data: Dict[str, Union[int, str]] = {
        'id': chat.id,
        'name': chat.name
    }
    return jsonify(response_data)


@assistant_bp.route("/chats/<int:chat_id>", methods=["DELETE"])
def delete_chat(chat_id: int):
    chat = cast(Chat, Chat.query.get(chat_id))
    if not chat:
        return jsonify({
            'success': False,
            'error': 'Чат не найден'
        })
    db.session.delete(chat)
    db.session.commit()
    return jsonify({
        'success': True
    })


@assistant_bp.route("/chats/<int:chat_id>/rename", methods=["POST"])
def rename_chat(chat_id: int):
    request_data = request.get_json()
    new_name = request_data.get('name', 'New Chat')
    chat = cast(Chat, Chat.query.get(chat_id))
    if not chat:
        return jsonify({
            'success': False,
            'error': 'Чат не найден'
        })
    chat.name = new_name
    db.session.commit()
    return jsonify({
        'success': True,
        'id': chat.id,
        'name': chat.name
    })


@assistant_bp.route("/history/<int:chat_id>", methods=["GET"])
def chat_history(chat_id: int):
    chat = cast(Chat, Chat.query.get(chat_id))
    messages = cast(List[Message], chat.messages)
    messages_data = []
    for message in messages:
        if message.role == 'context':
            continue
        content = message.content
        if message.role == 'assistant':
            content = markdown_process(content)
        messages_data.append({
            'role': message.role,
            'content': content,
        })
    return jsonify({
        'history': messages_data
    })


@assistant_bp.route("/save_message/<int:chat_id>", methods=["POST"])
def save_message(chat_id: int):
    request_data = request.get_json()
    role = request_data.get('role', 'user')
    content = request_data.get('content', '')
    chat = cast(Chat, Chat.query.get(chat_id))
    if not chat:
        return jsonify({
            'success': False,
            'error': 'Чат не найден'
        })
    message = Message(role=role, content=content, chat=chat)
    db.session.add(message)
    db.session.commit()
    return jsonify({
        'success': True,
        'message': {
            'role': message.role,
            'content': message.content
        }
    })


@assistant_bp.route("/ask/<int:chat_id>", methods=["POST"])
def ask(chat_id: int):
    text_generator = current_app.dependencies['text_generator']
    request_data = request.get_json()

    question = request_data.get('prompt', '')
    chat = cast(Chat, Chat.query.get(chat_id))

    if 'context' in request_data:
        print('[DEBUG] Обновление контекста чата')
        context_str = request_data.get('context', '')
        context_json = json.loads(context_str, strict=False)
        context_html = html.render(context_json['ops'])
        context_message = chat.messages[0]
        context_message.content = context_html
        db.session.commit()

    if not chat:
        return jsonify({
            'success': False,
            'error': 'Ошибка генерации ответа: чат не найден'
        })
    history: HistoryData = []
    for message in chat.messages:
        db_role = message.role
        if db_role == 'system-info':
            continue  # Skip system-info messages
        role = db_role
        if db_role == 'context':
            role = 'system'
        history.append({
            'role': role,
            'content': message.content
        })
    answer = text_generator.generate(history)

    message = Message(role='assistant', content=answer, chat=chat)
    db.session.add(message)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': {
            'role': message.role,
            'content': message.content
        }
    })
