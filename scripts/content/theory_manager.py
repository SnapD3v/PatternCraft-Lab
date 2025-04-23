"""
Description: Manages the organization and retrieval of theoretical content blocks
and their associated text content. Handles theory text operations and block
management.
"""

from typing import Dict, Any, Optional, Tuple, List
import json
import scripts.database as db
from .content_manager import ContentManager


class TheoryManager(ContentManager):
    def __init__(self, session_factory: db.sessionmaker[db.Session]) -> None:
        self.session_factory = session_factory

    def add_theory_text(
        self, name: str, content: str, description: str, image_url: str, block_id: int
    ) -> Tuple[bool, Optional[str]]:
        session = self.session_factory()
        texts_block = (
            session.query(db.TextsBlock).filter(db.TextsBlock.id == block_id).first()
        )

        theory_text = db.TheoryText(
            name=name, content=content, description=description, image_url=image_url
        )

        if texts_block:
            texts_block.texts.append(theory_text)
        else:
            raise TypeError

        session.commit()
        session.close()

        return True, None

    def add_texts_block(
        self, name: str, description: str
    ) -> Tuple[bool, Optional[str]]:
        session = self.session_factory()
        texts_block = db.TextsBlock(name=name, description=description)

        session.add(texts_block)
        session.commit()
        session.close()

        return True, None

    def edit(
        self, model: db.Base, id: int, **kwargs: Dict[str, str]
    ) -> Tuple[bool, Optional[str]]:
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
        result: List[db.TextsBlock] = (
            session.query(db.TextsBlock)
            .options(db.joinedload(db.TextsBlock.texts))
            .all()
        )
        session.close()
        return result

    def get_theory(self, theory_text_id: int) -> db.TheoryText:
        session = self.session_factory()
        result: db.TheoryText = session.query(
            db.TheoryText.id == theory_text_id
        ).first()
        session.close()
        return result
