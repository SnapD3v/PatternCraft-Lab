from app import ProblemService, PatternCraftAuthClient
from app.database import Problem, Test, db
tests_code = """def test():
    assert 1 == 1
"""

class ServiceAdapter:
    def __init__(self,auth_client: PatternCraftAuthClient):
        self.client = auth_client
    def download_problem(self, problem_id: int) -> Problem:
        data = self.client.request('GET', f"/api/problems/{problem_id}")

        problem_json = data.json()
        problem = Problem(
            id=int(problem_json['id']),
            name=problem_json["name"],
            task=problem_json["description"],
            tags=str(problem_json["tags_json"]) or "[]",
            difficulty=problem_json['difficulty']
        )
        test = Test(code=tests_code)
        problem.tests.append(test)
        db.session.add(problem)
        db.session.commit()
        db.session.refresh(problem)

        return problem
