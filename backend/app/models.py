from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    username_enc: Mapped[str] = mapped_column(Text)
    email_enc: Mapped[str] = mapped_column(Text)
    full_name_enc: Mapped[str] = mapped_column(Text)
    password_hash: Mapped[str] = mapped_column(String(255))
    age: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(String(20), default="user")  # user | admin
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | blocked
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    negotiations_as_p1: Mapped[list["Negotiation"]] = relationship(
        back_populates="participant1",
        foreign_keys="Negotiation.participant1_id",
    )
    negotiations_as_p2: Mapped[list["Negotiation"]] = relationship(
        back_populates="participant2",
        foreign_keys="Negotiation.participant2_id",
    )
    score_points: Mapped[list["ScorePoint"]] = relationship(back_populates="user")


class Negotiation(Base):
    __tablename__ = "negotiations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mode: Mapped[str] = mapped_column(String(20))  # ai | human
    difficulty: Mapped[str] = mapped_column(String(20), default="easy")
    scenario_id: Mapped[str] = mapped_column(String(64))
    scenario_title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default="active")
    # active | searching | pending_review | reviewed | cancelled
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    participant1_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    participant2_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    current_turn_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    turn_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    participant1: Mapped[User] = relationship(
        back_populates="negotiations_as_p1",
        foreign_keys=[participant1_id],
    )
    participant2: Mapped[User | None] = relationship(
        back_populates="negotiations_as_p2",
        foreign_keys=[participant2_id],
    )
    messages: Mapped[list["Message"]] = relationship(
        back_populates="negotiation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    negotiation_id: Mapped[int] = mapped_column(ForeignKey("negotiations.id"), index=True)
    sender_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    sender_type: Mapped[str] = mapped_column(String(20))  # user | ai | system
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    negotiation: Mapped[Negotiation] = relationship(back_populates="messages")


class MatchTicket(Base):
    """Очередь поиска оппонента. Хранится в БД, чтобы работать на shared-хостинге без WebSocket."""

    __tablename__ = "match_tickets"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(64), index=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="easy")
    negotiation_id: Mapped[int | None] = mapped_column(ForeignKey("negotiations.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ScorePoint(Base):
    __tablename__ = "score_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    negotiation_id: Mapped[int | None] = mapped_column(ForeignKey("negotiations.id"), nullable=True)
    score: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="score_points")
