"""
Description: Manages the behavior of the AI tutor
"""

from typing import List, Optional, Dict
from datetime import datetime
import app.database as db
from .content_manager import ContentManager
from ..ai.agents import Agent
from ..dto.chat_history_dto import ChatHistoryDTO
from ..utils.markdown_utils import strip_markdown


class AssistantManager(ContentManager):
    def __init__(
        self,
        session_factory: db.sessionmaker[db.Session],
        assistant: Agent,
    ) -> None:
        self.session_factory = session_factory
        self.assistant = assistant

    def create_chat(self, name: str) -> int:
        session = self.session_factory()
        try:
            chat = db.Chat(name=name)
            session.add(chat)
            session.commit()
            return chat.id
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def get_chats(self) -> List[Dict]:
        session = self.session_factory()
        try:
            chats = session.query(db.Chat).order_by(db.Chat.updated_at.desc()).all()
            return [{"id": chat.id, "name": chat.name, "updated_at": chat.updated_at} for chat in chats]
        finally:
            session.close()

    def rename_chat(self, chat_id: int, new_name: str) -> None:
        session = self.session_factory()
        try:
            chat = session.query(db.Chat).filter(db.Chat.id == chat_id).first()
            if chat:
                chat.name = new_name
                session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_chat(self, chat_id: int) -> None:
        session = self.session_factory()
        try:
            chat = session.query(db.Chat).filter(db.Chat.id == chat_id).first()
            if chat:
                session.delete(chat)
                session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def get_promt(self, chat_id: int, user_prompt: str) -> None:
        session = self.session_factory()
        try:
            chat = session.query(db.Chat).filter(db.Chat.id == chat_id).first()
            if not chat:
                raise ValueError("Chat not found")

            user_message_db = db.ChatHistory(
                role="user",
                content=user_prompt,
                chat_id=chat_id
            )
            session.add(user_message_db)

            chat.updated_at = datetime.now()
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def get_answer(self, chat_id: int, user_prompt: str) -> str:
        session = self.session_factory()
        try:
            chat = session.query(db.Chat).filter(db.Chat.id == chat_id).first()
            if not chat:
                raise ValueError("Chat not found")

            db_messages = (
                session.query(db.ChatHistory)
                .filter(db.ChatHistory.chat_id == chat_id)
                .order_by(db.ChatHistory.id)
                .all()
            )
            history = []
            for message in db_messages:
                history_line = {"role": message.role, "content": strip_markdown(message.content)}
                history.append(history_line)

            answer = self.assistant.generate(history=history, user_prompt=user_prompt)

            assistant_message_db = db.ChatHistory(
                role="assistant",
                content=answer,
                chat_id=chat_id
            )
            session.add(assistant_message_db)

            chat.updated_at = datetime.now()
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

        return answer

    def get_all_messages(self, chat_id: int) -> Optional[List[ChatHistoryDTO]]:
        session = self.session_factory()
        try:
            messages_db = (
                session.query(db.ChatHistory)
                .filter(db.ChatHistory.chat_id == chat_id)
                .order_by(db.ChatHistory.id)
                .all()
            )
            if messages_db:
                return [ChatHistoryDTO(msg) for msg in messages_db]
            return None
        finally:
            session.close()

    def get_message(self, chat_id: int, message_id: int) -> Optional[ChatHistoryDTO]:
        session = self.session_factory()
        try:
            message_db = (
                session.query(db.ChatHistory)
                .filter(db.ChatHistory.chat_id == chat_id)
                .filter(db.ChatHistory.id == message_id)
                .first()
            )
            if message_db:
                return ChatHistoryDTO(message_db)
            return None
        finally:
            session.close()

    def clear_history(self, chat_id: int) -> None:
        session = self.session_factory()
        try:
            session.query(db.ChatHistory).filter(db.ChatHistory.chat_id == chat_id).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def save_user_message(self, chat_id: int, content: str) -> None:
        session = self.session_factory()
        try:
            user_message_db = db.ChatHistory(
                role="user",
                content=content,
                chat_id=chat_id
            )
            session.add(user_message_db)
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
