from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, user_to_public
from ..models import User
from ..schemas import LoginRequest, ProfileUpdateRequest, RegisterRequest, TokenResponse, UserPublic
from ..security import (
    create_access_token,
    encrypt_text,
    hash_lookup,
    hash_password,
    verify_password,
)
from ..services.scoring import week_score_series

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    username_hash = hash_lookup(payload.username)
    email_hash = hash_lookup(payload.email)
    exists = db.scalar(
        select(User).where(or_(User.username_hash == username_hash, User.email_hash == email_hash))
    )
    if exists:
        raise HTTPException(status_code=400, detail="Логин или почта уже заняты")

    user = User(
        username_hash=username_hash,
        email_hash=email_hash,
        username_enc=encrypt_text(payload.username.strip()),
        email_enc=encrypt_text(payload.email.lower().strip()),
        full_name_enc=encrypt_text(payload.full_name.strip()),
        password_hash=hash_password(payload.password),
        age=payload.age,
        role="user",
        status="active",
        overall_score=0.0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(str(user.id), {"role": user.role})
    return TokenResponse(access_token=token, role=user.role)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    lookup = hash_lookup(payload.login)
    user = db.scalar(
        select(User).where(or_(User.username_hash == lookup, User.email_hash == lookup))
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="Аккаунт заблокирован")
    token = create_access_token(str(user.id), {"role": user.role})
    return TokenResponse(access_token=token, role=user.role)


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(get_current_user)):
    return user_to_public(user)


profile_router = APIRouter(prefix="/api/profile", tags=["profile"])


@profile_router.get("/me")
def get_my_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = user_to_public(user)
    data["week_scores"] = week_score_series(db, user.id)
    return data


@profile_router.patch("/me")
def update_my_profile(
    payload: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.username:
        new_hash = hash_lookup(payload.username)
        clash = db.scalar(
            select(User).where(User.username_hash == new_hash, User.id != user.id)
        )
        if clash:
            raise HTTPException(status_code=400, detail="Логин уже занят")
        user.username_hash = new_hash
        user.username_enc = encrypt_text(payload.username.strip())

    if payload.email:
        new_hash = hash_lookup(payload.email)
        clash = db.scalar(
            select(User).where(User.email_hash == new_hash, User.id != user.id)
        )
        if clash:
            raise HTTPException(status_code=400, detail="Почта уже занята")
        user.email_hash = new_hash
        user.email_enc = encrypt_text(payload.email.lower().strip())

    if payload.full_name:
        user.full_name_enc = encrypt_text(payload.full_name.strip())
    if payload.age is not None:
        user.age = payload.age
    if payload.password:
        user.password_hash = hash_password(payload.password)

    db.add(user)
    db.commit()
    db.refresh(user)
    data = user_to_public(user)
    data["week_scores"] = week_score_series(db, user.id)
    return data
