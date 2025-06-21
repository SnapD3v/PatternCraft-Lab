from __future__ import annotations

from typing import List, Optional
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    Boolean,
    Enum,
    Table,
    Column
)

from .constants import Difficulty, Language

# Убираем создание отдельного Flask приложения
db = SQLAlchemy()


class TextsBlock(db.Model):
    __tablename__ = 'texts_blocks'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    in_practice: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default='1',
        nullable=False
    )
    texts: Mapped[List[TheoryText]] = relationship(
        "TheoryText", back_populates="block",
        cascade="all, delete-orphan")


class TheoryText(db.Model):
    __tablename__ = 'theory_texts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    image_url: Mapped[str] = mapped_column(String, nullable=True)
    in_practice: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default='1',
        nullable=False
    )
    block_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('texts_blocks.id'),
        nullable=False
    )

    block: Mapped[TextsBlock] = relationship(
        TextsBlock, back_populates="texts")


class Problem(db.Model):
    __tablename__ = 'problems'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    task: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[Language] = mapped_column(
        Enum(Language, name="language_enum"),
        nullable=False,
        default=Language.PYTHON,
        server_default=Language.PYTHON.name
    )
    difficulty: Mapped[Difficulty] = mapped_column(
        Enum(Difficulty, name="difficulty_enum"),  # вот здесь!
        nullable=False,
        default=Difficulty.EASY,  # значение по умолчанию можно Enum'ом
        server_default=Difficulty.EASY.name  # или строкой
    )
    server_problem_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    is_solved: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    solutions: Mapped[List["Solution"]] = relationship(
        "Solution", back_populates="problem", cascade="all, delete-orphan"
    )
    tests: Mapped[List["Test"]] = relationship(
        "Test", back_populates="problem", cascade="all, delete-orphan"
    )


class Solution(db.Model):
    __tablename__ = 'solutions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    problem_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('problems.id'),
        nullable=False
    )

    problem: Mapped[Problem] = relationship(
        Problem, back_populates="solutions"
    )
    review: Mapped["Review"] = relationship(
        "Review",
        back_populates="solution",
        cascade="all, delete-orphan",
        uselist=False
    )


class Review(db.Model):
    __tablename__ = 'reviews'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tests_results: Mapped[str] = mapped_column(
        Text, nullable=True
    )
    # Исправляем тип для is_solved
    is_solved: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    solution_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('solutions.id'),
        nullable=False
    )

    solution: Mapped[Solution] = relationship(
        Solution, back_populates="review")


class Test(db.Model):
    __tablename__ = 'tests'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    problem_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('problems.id'),
        nullable=False
    )

    problem: Mapped[Problem] = relationship(
        Problem, back_populates="tests"
    )


class Chat(db.Model):
    __tablename__ = 'chats'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now
    )

    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan"
    )


class Message(db.Model):
    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chat_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('chats.id'),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now
    )

    chat: Mapped[Chat] = relationship("Chat", back_populates="messages")


course_problems = Table(
    'course_problems',
    db.Model.metadata,
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True),
    Column('problem_id', Integer, ForeignKey('problems.id'), primary_key=True)
)

course_theories = Table(
    'course_theories',
    db.Model.metadata,
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True),
    Column(
        'theory_id',
        Integer,
        ForeignKey('theory_texts.id'),
        primary_key=True
    )
)


class Course(db.Model):
    __tablename__ = 'courses'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )
    server_course_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    creator_id: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False
    )
    is_hidden: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default='0',
        nullable=False
    )

    problems: Mapped[List["Problem"]] = relationship(
        "Problem",
        secondary=course_problems,
        backref="courses"
    )
    theories: Mapped[List["TheoryText"]] = relationship(
        "TheoryText",
        secondary=course_theories,
        backref="courses"
    )
