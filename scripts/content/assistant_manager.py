"""
Description: Manages the behavior of the AI tutor
"""

from typing import List, Optional
import scripts.database as db
from .content_manager import ContentManager
from ..ai.agents import Agent
from ..dto.chat_history_dto import ChatHistoryDTO


class AssistantManager(ContentManager):
    def __init__(
        self,
        session_factory: db.sessionmaker[db.Session],
        assistant: Agent,
    ) -> None:
        self.session_factory = session_factory
        self.assistant = assistant

    def get_promt(self, user_prompt: str) -> None:
        session = self.session_factory()
        try:
            user_message_db = db.ChatHistory(
                role="user",
                content=user_prompt,
            )
            session.add(user_message_db)
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()


    def get_answer(self, user_prompt: str) -> str:
        session = self.session_factory()
        try:
            db_messages = (
                session.query(db.ChatHistory).order_by(db.ChatHistory.id).all()
            )
            history = []
            for message in db_messages:
                history_line = {"role": message.role, "content": message.content}
                history.append(history_line)

            answer = self.assistant.generate(history=history, user_prompt=user_prompt)

            assistant_message_db = db.ChatHistory(
                role="assistant",
                content=answer,
            )
            session.add(assistant_message_db)

            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

        return answer

    def get_all_messages(self) -> Optional[List[ChatHistoryDTO]]:
        session = self.session_factory()
        try:
            messages_db = (
                session.query(db.ChatHistory).order_by(db.ChatHistory.id).all()
            )
            if messages_db:
                return [ChatHistoryDTO(msg) for msg in messages_db]
            return None
        finally:
            session.close()

    def get_message(self, message_id: int) -> Optional[ChatHistoryDTO]:
        session = self.session_factory()
        try:
            message_db = (
                session.query(db.ChatHistory)
                .filter(db.ChatHistory.id == message_id)
                .first()
            )
            if message_db:
                return ChatHistoryDTO(message_db)
            return None
        finally:
            session.close()

    def clear_history(self) -> None:
        session = self.session_factory()
        try:
            session.query(db.ChatHistory).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
