"""
Description: Defines all web routes and their handlers for the application. Includes
routes for theory content, problems, and solution history management.
"""

import threading
from flask import Flask, render_template, request, redirect, jsonify
from .route_provider import IRouteProvider
from ..content.theory_manager import TheoryManager
from ..content.problems_manager import ProblemsManager
from ..content.assistant_manager import AssistantManager
import markdown


class WebRoutes(IRouteProvider):
    def __init__(
        self,
        theory_manager: TheoryManager,
        problems_manager: ProblemsManager,
        assistant_manager: AssistantManager,
        tags: list,
    ) -> None:
        self.theory_manager = theory_manager
        self.problems_manager = problems_manager
        self.assistant_manager = assistant_manager
        self.tags = tags

    def register(self, app: Flask) -> None:
        app.add_url_rule("/", view_func=self.index, methods=["GET"])
        app.add_url_rule(
            "/theory", view_func=self.theory_list, methods=["GET"])
        app.add_url_rule("/problems", view_func=self.problems, methods=["GET"])
        app.add_url_rule(
            "/create/problem", view_func=self.create_problem, methods=["GET", "POST"]
        )
        app.add_url_rule("/theory/<int:id>",
                         view_func=self.theory, methods=["GET"])
        app.add_url_rule(
            "/problem/<int:id>", view_func=self.problem, methods=["GET", "POST"]
        )

        # Маршруты для Assistant API
        app.add_url_rule(
            "/assistant/ask/<int:chat_id>", view_func=self.assistant_ask, methods=["POST"]
        )
        app.add_url_rule(
            "/assistant/history/<int:chat_id>", view_func=self.assistant_history, methods=["GET"]
        )
        app.add_url_rule(
            "/assistant/clear/<int:chat_id>", view_func=self.assistant_clear_history, methods=["POST"]
        )
        app.add_url_rule(
            "/assistant/format_promt/<int:chat_id>", view_func=self.server_promt_processing, methods=["POST"]
        )
        app.add_url_rule(
            "/assistant/save_message/<int:chat_id>", view_func=self.save_user_message, methods=["POST"]
        )

        # Маршруты для управления чатами
        app.add_url_rule(
            "/assistant/chats", view_func=self.get_chats, methods=["GET"]
        )
        app.add_url_rule(
            "/assistant/chats/create", view_func=self.create_chat, methods=["POST"]
        )
        app.add_url_rule(
            "/assistant/chats/<int:chat_id>", view_func=self.delete_chat, methods=["DELETE"]
        )
        app.add_url_rule(
            "/assistant/chats/<int:chat_id>/rename", view_func=self.rename_chat, methods=["POST"]
        )

    def index(self) -> str:
        return render_template("index.html")

    def problems(self) -> str:
        problems = self.problems_manager.get_problems()
        return render_template("problems.html", problems=problems)

    def problem(self, id: int) -> str:
        problem = self.problems_manager.get_problem(id)
        if request.method == "GET":
            return render_template("problem.html", problem=problem)

        solution = request.form["solution"]
        threading.Thread(
            target=self.problems_manager.review_solution,
            args=(
                id,
                solution,
            ),
            daemon=True,
        ).start()
        return redirect(f"/problem/{id}")

    def create_problem(self) -> str:
        if request.method == "GET":
            return render_template("create_problem.html", tags=self.tags)

        tags = request.form["selected_tags"].split(",")
        threading.Thread(
            target=self.problems_manager.create_problem, args=(
                tags,), daemon=True
        ).start()
        return redirect("/problems")

    def theory_list(self) -> str:
        theory_list = self.theory_manager.get_texts_blocks()
        return render_template("theory_list.html", theory=theory_list)

    def theory(self, id: int) -> str:
        theory = self.theory_manager.get_theory(id)
        return render_template("theory.html", theory=theory)

    # --- Assistant API Handlers ---
    def server_promt_processing(self, chat_id):
        data = request.get_json()
        user_prompt = data.get("prompt")
        if not user_prompt:
            return jsonify({"error": "Prompt is required"}), 400

        try:
            self.assistant_manager.get_promt(chat_id, user_prompt)
            html_prompt = markdown.markdown(
                user_prompt, extensions=["fenced_code", "nl2br"]
            )
            return jsonify({"promt": html_prompt})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def assistant_ask(self, chat_id):
        data = request.get_json()
        user_prompt = data.get("prompt")
        if not user_prompt:
            return jsonify({"error": "Prompt is required"}), 400

        try:
            raw_answer = self.assistant_manager.get_answer(chat_id, user_prompt)
            html_answer = markdown.markdown(
                raw_answer, extensions=["fenced_code", "nl2br"]
            )
            return jsonify({"answer": html_answer})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def assistant_history(self, chat_id):
        try:
            messages = self.assistant_manager.get_all_messages(chat_id)
            history_data = []
            if messages:
                for msg_dto in messages:
                    history_data.append(
                        {"role": msg_dto.role, "content": msg_dto.content}
                    )
            return jsonify({"history": history_data})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def assistant_clear_history(self, chat_id):
        try:
            self.assistant_manager.clear_history(chat_id)
            return jsonify({"status": "success", "message": "Chat history cleared."})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def save_user_message(self, chat_id):
        data = request.get_json()
        content = data.get("content")
        if not content:
            return jsonify({"error": "Content is required"}), 400
        try:
            self.assistant_manager.save_user_message(chat_id, content)
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # --- Chat Management Handlers ---
    def get_chats(self):
        try:
            chats = self.assistant_manager.get_chats()
            return jsonify({"chats": chats})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def create_chat(self):
        data = request.get_json()
        name = data.get("name", "New Chat")
        try:
            chat_id = self.assistant_manager.create_chat(name)
            return jsonify({"id": chat_id, "name": name})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def rename_chat(self, chat_id):
        data = request.get_json()
        new_name = data.get("name")
        if not new_name:
            return jsonify({"error": "Name is required"}), 400

        try:
            self.assistant_manager.rename_chat(chat_id, new_name)
            return jsonify({"status": "success", "message": "Chat renamed."})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def delete_chat(self, chat_id):
        try:
            self.assistant_manager.delete_chat(chat_id)
            return jsonify({"status": "success", "message": "Chat deleted."})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
