from typing import Dict, Any, Optional, Tuple, Type, List
from abc import ABC, abstractmethod
import threading

from flask import Flask, render_template, request, redirect
import json
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
import markdown
import re

import database as db


def strip_markdown(md_text: str) -> str:
    md_text = re.sub(r'[#*_`>\-\+]+', '', md_text)
    md_text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', md_text)  # ссылки
    return md_text.strip()


class ITextGenerator(ABC):
    @abstractmethod
    def generate(self, history: List[ChatCompletionMessageParam], model: Optional[str] = None) -> str:
        pass


class TextGenerator(ITextGenerator):
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        self.model = model

    def generate(self, history: List[ChatCompletionMessageParam], model: Optional[str] = None) -> str:
        model = model or self.model
        completion = self.client.chat.completions.create(
            model=model,
            messages=history
        )
        if completion.choices[0].message.content:
            return completion.choices[0].message.content
        raise TypeError


class ContentManager(ABC):
    pass


class TheoryManager(ContentManager):
    def __init__(self, session_factory: db.sessionmaker[db.Session]) -> None:
        self.session_factory = session_factory

    def add_theory_text(self, name: str, content: str, description: str, image_url: str, block_id: int) -> Tuple[bool, Optional[str]]:
        session = self.session_factory()
        texts_block = session.query(db.TextsBlock).filter(
            db.TextsBlock.id == block_id).first()

        theory_text = db.TheoryText(
            name=name,
            content=content,
            description=description,
            image_url=image_url
        )

        if texts_block:
            texts_block.texts.append(theory_text)
        else:
            raise TypeError

        session.commit()
        session.close()

        return True, None

    def add_texts_block(self, name: str, description: str) -> Tuple[bool, Optional[str]]:
        session = self.session_factory()
        texts_block = db.TextsBlock(
            name=name,
            description=description
        )

        session.add(texts_block)
        session.commit()
        session.close()

        return True, None

    def edit(self, model: db.Base, id: int, **kwargs: Dict[str, str]) -> Tuple[bool, Optional[str]]:
        session = self.session_factory()
        try:
            instance: Any = session.query(model).filter(model.id == id).first()
            if not instance:
                return False, f"{model.__name__} with id={id} not found"

            for field_name, new_value in kwargs.items():
                if hasattr(instance, field_name):
                    setattr(instance, field_name, new_value)
                else:
                    return False, f"Field '{field_name}' not found on {model.__name__}"

            session.commit()
            return True, None
        except Exception as e:
            session.rollback()
            return False, str(e)

    def get_texts_blocks(self) -> List[db.TextsBlock]:
        session = self.session_factory()
        result: List[db.TextsBlock] = session.query(db.TextsBlock).options(
            db.joinedload(db.TextsBlock.texts)).all()
        session.close()
        return result

    def get_theory(self, theory_text_id: int) -> db.TheoryText:
        session = self.session_factory()
        result: db.TheoryText = session.query(
            db.TheoryText.id == theory_text_id).first()
        session.close()
        return result


class SolutionHistoryElementDTO:
    def __init__(self, solution_history_element: db.SolutionHistoryElement) -> None:
        self.id = solution_history_element.id
        self.type = str(solution_history_element.type)
        if self.type == 'text':
            raw_content = str(solution_history_element.content)
            self.content = markdown.markdown(
                raw_content, extensions=['fenced_code', 'nl2br'])
        else:
            self.content = solution_history_element.content


class ProblemDTO:
    def __init__(self, problem: db.Problem) -> None:
        self.id = problem.id
        raw_name = str(problem.name)
        self.name = strip_markdown(raw_name)
        raw_task = str(problem.task)
        self.task = markdown.markdown(
            raw_task, extensions=['fenced_code', 'nl2br'])
        self.tags = self._parse_tags(problem.block.tags_json)
        self.solution_history_elements = [SolutionHistoryElementDTO(
            i) for i in problem.solution_history_elements]

    def _parse_tags(self, tags_json: str) -> List[str]:
        try:
            return json.loads(tags_json)
        except (json.JSONDecodeError, TypeError):
            return []


class Agent(ABC):
    @abstractmethod
    def generate(self, history: List[ChatCompletionMessageParam], **kwargs: Dict[str, Any]) -> Any:
        pass


class TaskWriter(Agent):
    def __init__(self, text_generator: ITextGenerator, system_prompt: str, user_prompt: str) -> None:
        self.text_generator = text_generator
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt

    def _prepare_history(self, history: List[Dict[str, str]], tags: List[str]) -> None:
        history.insert(
            0,
            {
                'role': 'system',
                'content': self.system_prompt
            }
        )

        joined_tags = ', '.join(tags)

        history.append(
            {
                'role': 'user',
                'content': self.user_prompt.format(tags=joined_tags)
            }
        )

    def generate(self, history: List[ChatCompletionMessageParam], **kwargs: Dict[str, Any]) -> Tuple[str, str]:
        self._prepare_history(history, tags=kwargs['tags'])
        response = self.text_generator.generate(history)
        name = response.split('\n')[0]
        task = response.lstrip(name).strip()
        return name, task


class Reviewer(Agent):
    def __init__(self, text_generator: ITextGenerator, system_prompt: str) -> None:
        self.text_generator = text_generator
        self.system_prompt = system_prompt

    def _prepare_history(self, history: List[Dict[str, str]], tags: List[str], solution: str) -> None:
        joined_tags = ', '.join(tags)

        history.insert(
            0,
            {
                'role': 'system',
                'content': self.system_prompt.format(tags=joined_tags)
            }
        )

        history.append(
            {
                'role': 'user',
                'content': solution
            }
        )

    def generate(self, history: List[Dict[str, str]], **kwargs: Dict[str, Any]) -> str:
        self._prepare_history(
            history, tags=kwargs['tags'], solution=kwargs['solution'])
        review = self.text_generator.generate(history)
        return review


class ProblemsManager(ContentManager):
    def __init__(self, session_factory: db.sessionmaker[db.Session], task_writer: Agent, reviewer: Agent) -> None:
        self.session_factory = session_factory
        self.task_writer = task_writer
        self.reviewer = reviewer

    def get_problems_set(self, tags: List[str]) -> int:
        session = self.session_factory()
        tags_json = json.dumps(tags)
        problems_set = session.query(db.ProblemsSet).filter(
            db.ProblemsSet.tags_json == tags_json).first()
        if problems_set:
            return problems_set.id

        problems_set = db.ProblemsSet(
            tags_json=tags_json
        )
        session.add(problems_set)
        session.commit()
        result = problems_set.id

        session.close()
        return result

    def create_problem(self, tags: List[str]) -> int:
        session = self.session_factory()
        problems_set_id = self.get_problems_set(tags)
        problems_set = session.query(db.ProblemsSet).filter(
            db.ProblemsSet.id == problems_set_id).first()
        existing_problems = problems_set.problems
        history: List[Dict[str, str]] = []
        for problem in existing_problems:
            history_line = {
                'role': 'user',
                'content': problem.task
            }
            history.append(history_line)
        name, task = self.task_writer.generate(history, tags=tags)
        problem = db.Problem(
            name=name,
            task=task
        )
        problems_set.problems.append(problem)
        session.commit()

        result = problem.id

        session.close()
        return result

    def review_solution(self, problem_id: int, solution: str) -> str:
        session = self.session_factory()
        problem = session.query(db.Problem).filter(
            db.Problem.id == problem_id).first()
        history: List[Dict[str, str]] = [
            {
                'role': 'assistant',
                'content': problem.task
            }
        ]
        for solution_history_element in problem.solution_history_elements:
            role = 'assitant' if solution_history_element.id % 2 == 0 else 'user'
            history_line = {
                'role': role,
                'content': solution_history_element.content
            }
            history.append(history_line)

        tags = json.loads(problem.block.tags_json)

        review = self.reviewer.generate(history, tags=tags, solution=solution)

        solution_history_element = db.SolutionHistoryElement(
            content=solution,
            type='code'
        )
        problem.solution_history_elements.append(solution_history_element)

        solution_history_element = db.SolutionHistoryElement(
            content=review,
            type='text'
        )
        problem.solution_history_elements.append(solution_history_element)
        session.commit()
        session.close()

        return review

    def get_problems(self) -> List[ProblemDTO]:
        session = self.session_factory()
        problems = session.query(db.Problem).options(
            db.joinedload(db.Problem.block),
            db.joinedload(db.Problem.solution_history_elements)
        ).all()
        session.close()
        return [ProblemDTO(problem) for problem in problems]

    def get_problem(self, id: int) -> ProblemDTO:
        session = self.session_factory()
        problem = session.query(db.Problem).filter(db.Problem.id == id).options(
            db.joinedload(db.Problem.block),
            db.joinedload(db.Problem.solution_history_elements)
        ).first()
        session.close()
        return ProblemDTO(problem)


class IRouteProvider(ABC):
    @abstractmethod
    def register(self, app: Flask) -> None:
        pass


class WebRoutes(IRouteProvider):
    def __init__(self, theory_manager, problems_manager, tags):
        self.theory_manager = theory_manager
        self.problems_manager = problems_manager
        self.tags = tags

    def register(self, app: Flask) -> None:
        app.add_url_rule("/", view_func=self.index, methods=["GET"])
        app.add_url_rule(
            "/theory", view_func=self.theory_list, methods=["GET"])
        app.add_url_rule("/problems", view_func=self.problems, methods=["GET"])
        app.add_url_rule(
            "/create/problem", view_func=self.create_problem, methods=["GET", "POST"])
        app.add_url_rule("/theory/<int:id>",
                         view_func=self.theory, methods=["GET"])
        app.add_url_rule("/problem/<int:id>",
                         view_func=self.problem, methods=["GET", "POST"])

    def index(self) -> str:
        return render_template('index.html')

    def problems(self) -> str:
        problems = self.problems_manager.get_problems()
        return render_template('problems.html', problems=problems)

    def problem(self, id: int) -> str:
        problem = self.problems_manager.get_problem(id)
        if request.method == 'GET':
            return render_template('problem.html', problem=problem)

        solution = request.form['solution']
        threading.Thread(
            target=self.problems_manager.review_solution,
            args=(id, solution,),
            daemon=True
        ).start()
        return redirect(f'/problem/{id}')

    def create_problem(self) -> str:
        if request.method == 'GET':
            return render_template('create_problem.html', tags=self.tags)

        tags = request.form['selected_tags'].split(',')
        threading.Thread(
            target=self.problems_manager.create_problem,
            args=(tags,),
            daemon=True
        ).start()
        return redirect('/problems')

    def theory_list(self) -> str:
        theory_list = self.theory_manager.get_texts_blocks()
        return render_template('theory_list.html', theory=theory_list)

    def theory(self, id: int) -> str:
        theory = self.theory_manager.get_theory(id)
        return render_template('theory.html', theory=theory)


class WebAppFactory:
    @staticmethod
    def create_app(routes: IRouteProvider) -> Flask:
        app = Flask(__name__)
        routes.register(app)
        return app


class AppRunner:
    def __init__(self, app: Flask, config: Dict[str, Any]) -> None:
        self.app = app
        self.config = config

    def run(self) -> None:
        self.app.run(**self.config)


if __name__ == '__main__':
    from config import settings
    from services.user_config import user_config_manager

    user_config = user_config_manager.get_config()

    user_config_manager.print_config()

    text_generator = TextGenerator(
        settings.defaults.base_url,
        user_config.api.api_key.get_secret_value(),
        user_config.api.model
    )

    theory_manager = TheoryManager(db.create_session)
    task_writer: Agent = TaskWriter(
        text_generator, settings.prompt.writer_system_prompt, settings.prompt.writer_user_prompt)
    reviewer: Agent = Reviewer(text_generator, settings.prompt.reviewer_prompt)

    problems_manager = ProblemsManager(
        db.create_session, task_writer, reviewer)

    routes = WebRoutes(theory_manager, problems_manager,
                       settings.tags.tags_list)
    app = WebAppFactory.create_app(routes)

    runner = AppRunner(app, settings.run.model_dump())

    runner.run()
