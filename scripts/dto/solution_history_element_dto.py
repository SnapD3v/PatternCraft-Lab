import markdown
import scripts.database as db


class SolutionHistoryElementDTO:
    def __init__(self, solution_history_element: db.SolutionHistoryElement) -> None:
        self.id = solution_history_element.id
        self.type = str(solution_history_element.type)
        if self.type == "text":
            raw_content = str(solution_history_element.content)
            self.content = markdown.markdown(
                raw_content, extensions=["fenced_code", "nl2br"]
            )
        else:
            self.content = solution_history_element.content
