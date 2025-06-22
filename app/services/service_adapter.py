from datetime import datetime
from app import ProblemService, PatternCraftAuthClient
from app.database import Course, Problem, Test, TextsBlock, TheoryText, db

tests_code = """def test():
    assert 1 == 1
"""


class ServiceAdapter:
    def __init__(self, auth_client: PatternCraftAuthClient):
        self.client = auth_client

    def download_problem(self, problem_id: int) -> Problem:
        data = self.client.request(
            "GET", f"/api/problems/{problem_id}", headers={"Accept": "application/json"}
        )

        problem_json = data.json()
        problem = Problem(
            id=int(problem_json["id"]),
            name=problem_json["name"],
            task=problem_json["description"],
            tags=str(problem_json["tags_json"]) or "[]",
            difficulty=problem_json["difficulty"],
        )
        test = Test(code=tests_code)
        problem.tests.append(test)
        db.session.add(problem)
        db.session.commit()
        db.session.refresh(problem)

        return problem

    def download_course(self, course_id: int) -> Course:
        data = self.client.request(
            "GET",
            f"/courses/api/{course_id}/download",
            headers={"Accept": "application/json"},
        )

        course_json = data.json()
        course_problems = []
        for p in course_json.get("problems", []):
            problem = Problem(
                name=p["name"],
                task=p["description"],
                tags=str(p["tags_json"]) or "[]",
                difficulty=p["difficulty"],
            )
            test = Test(code=tests_code)
            problem.tests.append(test)
            course_problems.append(problem)
        theories = []

        for t in course_json.get("theories", []):
            theory = TheoryText(
                name=t["name"],
                content=t["content"],
                description=t["description"],
                image_url=t["image_url"],
                in_practice=t["in_practice"],
            )
            theories.append(theory)

        course = Course(
            id=int(course_json["id"]),
            name=course_json["name"],
            description=course_json["description"],
            image_url=course_json["image_url"],
            server_course_id=int(course_json["id"]),
            creator_id=int(course_json["creator"]["id"]),
            created_at=datetime.fromisoformat(course_json["created_at"]),
            is_hidden=False,
            problems=course_problems,
            theories=theories,
        )

        db.session.add(course)
        db.session.commit()
        db.session.refresh(course)

        return course
