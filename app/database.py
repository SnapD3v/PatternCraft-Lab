"""
Description: Defines the database schema and models for the application. Contains
SQLAlchemy models for texts blocks, theory texts, problems sets, problems, and
solution history elements. Also provides database session creation functionality.
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship, sessionmaker, DeclarativeBase, Session, joinedload
from datetime import datetime


class Base(DeclarativeBase):
    pass


class TextsBlock(Base):
    __tablename__ = 'texts_blocks'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    texts = relationship("TheoryText", back_populates="block",
                         cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TextsBlock(id={self.id}, name={self.name})>"


class TheoryText(Base):
    __tablename__ = 'theory_texts'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    description = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    block_id = Column(Integer, ForeignKey('texts_blocks.id'), nullable=False)

    block = relationship("TextsBlock", back_populates="texts")

    def __repr__(self):
        return f"<TheoryText(id={self.id}, block_id={self.block_id})>"


class ProblemsSet(Base):
    __tablename__ = 'problems_set'

    id = Column(Integer, primary_key=True)
    tags_json = Column(String, nullable=False)

    problems = relationship(
        "Problem", back_populates="block", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ProblemsSet(id={self.id})>"


class Problem(Base):
    __tablename__ = 'problems'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    task = Column(Text, nullable=False)
    block_id = Column(Integer, ForeignKey('problems_set.id'), nullable=False)

    block = relationship("ProblemsSet", back_populates="problems")

    solution_history_elements = relationship(
        "SolutionHistoryElement", back_populates="problem", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Problem(id={self.id}, block_id={self.block_id})>"


class SolutionHistoryElement(Base):
    __tablename__ = 'solution_history_elements'

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    type = Column(String, nullable=False)
    problem_id = Column(Integer, ForeignKey('problems.id'), nullable=False)

    problem = relationship(
        "Problem", back_populates="solution_history_elements")

    def __repr__(self):
        return f"<SolutionHistoryElement(id={self.id}, problem_id={self.problem_id})>"
    

class Chat(Base):
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())

    messages = relationship("ChatHistory", back_populates="chat", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Chat(id={self.id}, name={self.name})>"


class ChatHistory(Base):
    __tablename__ = 'chat_history'

    id = Column(Integer, primary_key=True)
    role = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    chat_id = Column(Integer, ForeignKey('chats.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now())

    chat = relationship("Chat", back_populates="messages")

    def __repr__(self):
        return f"<ChatHistory(id={self.id}, chat_id={self.chat_id})>"


engine = create_engine("sqlite:///app.db", echo=True, future=True)
Base.metadata.create_all(engine)

create_session: sessionmaker[Session] = sessionmaker(bind=engine)
