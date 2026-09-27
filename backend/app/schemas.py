from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)
    age: int = Field(ge=14, le=100)


class LoginRequest(BaseModel):
    login: str  # username or email
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class UserPublic(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    age: int
    role: str
    status: str
    overall_score: float
    pii_ok: bool = True


class AdminUserOut(UserPublic):
    negotiations: list | None = None
    week_scores: list | None = None


class ProfileUpdateRequest(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=40)
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    age: int | None = Field(default=None, ge=14, le=100)
    password: str | None = Field(default=None, min_length=6, max_length=128)


class ScorePointOut(BaseModel):
    score: int
    created_at: datetime


class ProfileResponse(UserPublic):
    week_scores: list[ScorePointOut]


class ScenarioOut(BaseModel):
    id: str
    name: str
    desc: str
    locked: bool = False


class StartAiRequest(BaseModel):
    scenario_id: str
    difficulty: str = "easy"
    ai_starts: bool = False


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class MessageOut(BaseModel):
    id: int
    sender_id: int | None
    sender_type: str
    content: str
    created_at: datetime
    is_mine: bool = False
    sender_label: str | None = None


class ParticipantOut(BaseModel):
    id: int
    username: str
    full_name: str
    score: int | None = None


class NegotiationOut(BaseModel):
    id: int
    mode: str
    difficulty: str
    scenario_id: str
    scenario_title: str
    status: str
    score: int | None
    participant1_id: int
    participant2_id: int | None
    current_turn_user_id: int | None
    turn_deadline: datetime | None
    created_at: datetime
    finished_at: datetime | None
    messages: list[MessageOut] = []
    participants: list[ParticipantOut] = []


class NegotiationListItem(BaseModel):
    id: int
    mode: str
    difficulty: str
    scenario_title: str
    status: str
    score: int | None
    created_at: datetime
    finished_at: datetime | None
    message_count: int = 0
    participant_scores: list[ParticipantOut] = []


class ParticipantScoreIn(BaseModel):
    user_id: int
    score: int = Field(ge=1, le=100)


class ScoreRequest(BaseModel):
    """Одна оценка (AI) или список оценок по участникам (human)."""

    score: int | None = Field(default=None, ge=1, le=100)
    scores: list[ParticipantScoreIn] | None = None


class AdminUserUpdate(ProfileUpdateRequest):
    status: str | None = None
    role: str | None = None


class AdminUserCreate(RegisterRequest):
    is_admin: bool = False
