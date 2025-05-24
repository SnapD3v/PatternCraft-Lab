"""
Description: Defines data transfer objects for messages from assistant chat
"""

import markdown
import app.database as db


class ChatHistoryDTO:
    def __init__(self, message: db.ChatHistory) -> None:
        self.id = message.id
        self.role = message.role
        raw_content = str(message.content)
        self.content = markdown.markdown(
            raw_content, extensions=["fenced_code", "nl2br"]
        )