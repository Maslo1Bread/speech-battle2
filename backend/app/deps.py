from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .security import decode_access_token, decrypt_text

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется авторизация")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (ValueError, KeyError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен")

    user = db.get(User, user_id)
    if not user or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь недоступен")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только для администратора")
    return user


def _safe_decrypt(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    try:
        return decrypt_text(value)
    except ValueError:
        return fallback


def _try_decrypt_ok(value: str | None) -> bool:
    if not value:
        return False
    try:
        decrypt_text(value)
        return True
    except ValueError:
        return False


def user_to_public(user: User) -> dict:
    """Публичный профиль. Устойчив к смене SECRET_KEY (старые записи не роняют API)."""
    pii_ok = _try_decrypt_ok(user.username_enc)
    return {
        "id": user.id,
        "username": _safe_decrypt(user.username_enc, f"user#{user.id}"),
        "email": _safe_decrypt(user.email_enc, "—"),
        "full_name": _safe_decrypt(user.full_name_enc, f"Пользователь #{user.id}"),
        "age": user.age,
        "role": user.role,
        "status": user.status,
        "overall_score": round(user.overall_score or 0.0, 1),
        "pii_ok": pii_ok,
    }
