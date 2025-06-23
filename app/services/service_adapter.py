import base64
from datetime import datetime

from app import PatternCraftAuthClient
from app.database import Course, Problem, Test, TextsBlock, TheoryText, db


class ServiceAdapter:
    def __init__(self, auth_client: PatternCraftAuthClient):
        self.client = auth_client

    def download_problem(self, problem_id: int) -> Problem:
        problem = Problem.query.filter_by(server_problem_id=problem_id).first()
        if problem:
            return problem

        data = self.client.request(
            "GET", f"/api/problems/{problem_id}",
            headers={"Accept": "application/json"}
        )

        problem_json = data.json()
        tags_list = problem_json.get("tags_json", [])
        tags_str = ','.join(tags_list)
        problem = Problem(
            name=problem_json["name"],
            task=problem_json["description"],
            tags=tags_str,
            server_problem_id=int(problem_json["id"]),
            language=problem_json["language"],
            difficulty=problem_json["difficulty"],
        )
        tests_code = problem_json["tests"]
        test = Test(code=tests_code)
        problem.tests.append(test)
        db.session.add(problem)
        db.session.commit()
        db.session.refresh(problem)

        return problem

    def download_theory(self, theory_id: int) -> TheoryText:
        theory = TheoryText.query.filter_by(server_theory_id=theory_id).first()
        if theory:
            return theory

        data = self.client.request(
            "GET", f"/api/theories/{theory_id}", headers={"Accept": "application/json"}
        )

        theory_json = data.json()
        theory = TheoryText(
            name=theory_json["name"],
            description=theory_json["description"],
            content=theory_json["content"],
            server_theory_id=int(theory_json["id"]),
            image_url='',
        )

        db.session.add(theory)
        db.session.commit()

        if theory_json['image'].startswith('data:image/'):
            filename = 'app/static/img/theory/' + str(theory.id) + '.png'
            base64_data = theory_json["image"].split(',')[1]
            with open(filename, 'wb') as f:
                f.write(base64.b64decode(base64_data))
        else:
            theory.image_url = theory_json["image"]

        db.session.add(theory)
        db.session.commit()
        db.session.refresh(theory)

        return theory

    def download_course(self, course_id: int) -> Course:
        course = Course.query.filter_by(server_course_id=course_id).first()
        if course:
            return course

        data = self.client.request(
            "GET",
            f"/courses/api/{course_id}/download",
            headers={"Accept": "application/json"},
        )

        course_json = data.json()

        course = Course(
            name=course_json["name"],
            description=course_json["description"],
            image_url='',
            server_course_id=int(course_json["id"]),
            creator_id=int(course_json["creator"]["id"]),
            created_at=datetime.fromisoformat(course_json["created_at"]),
            is_hidden=course_json.get("is_hidden", False),
        )

        db.session.add(course)
        db.session.commit()

        if course_json['image'].startswith('data:image/'):
            filename = 'app/static/img/courses/' + str(course.id) + '.png'
            base64_data = course_json["image"].split(',')[1]
            with open(filename, 'wb') as f:
                f.write(base64.b64decode(base64_data))
        else:
            image_url = course_json["image"]
            course.image_url = image_url

        for problem_data in course_json.get("problems", []):
            print(problem_data)
            problem_id = problem_data.get("id")
            problem = self.download_problem(problem_id)
            course.problems.append(problem)

        texts_block = TextsBlock(
            name=f'Теория к курсу «{course_json["name"]}»',
            description=course_json['description'],
            in_practice=True
        )

        for theory_data in course_json.get("theories", []):
            theory_id = theory_data.get("id")
            theory = self.download_theory(theory_id)
            texts_block.texts.append(theory)
            course.theories.append(theory)

        db.session.add(texts_block)
        db.session.add(course)
        db.session.commit()
        db.session.refresh(course)

        return course
