from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from .config import ROOT_DIR, get_settings
from .database import Base, SessionLocal, engine
from .models import User
from .routers import admin, auth, negotiations, ws
from .security import encrypt_text, hash_lookup, hash_password

settings = get_settings()


def create_admin_if_needed() -> None:
    db = SessionLocal()
    try:
        admin_hash = hash_lookup(settings.admin_username)
        exists = db.scalar(select(User).where(User.username_hash == admin_hash))
        if exists:
            return
        admin = User(
            username_hash=admin_hash,
            email_hash=hash_lookup(settings.admin_email),
            username_enc=encrypt_text(settings.admin_username),
            email_enc=encrypt_text(settings.admin_email),
            full_name_enc=encrypt_text("Администратор"),
            password_hash=hash_password(settings.admin_password),
            age=30,
            role="admin",
            status="active",
            overall_score=0.0,
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()


def create_app() -> FastAPI:
    Base.metadata.create_all(bind=engine)
    create_admin_if_needed()

    app = FastAPI(title="Speech-Battle / Арена переговоров", version="1.0.0")
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins != ["*"] else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(auth.profile_router)
    app.include_router(negotiations.router)
    app.include_router(admin.router)
    app.include_router(ws.router)

    assets_dir = ROOT_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/")
    def root():
        return {
            "app": "Speech-Battle API",
            "version": "1.0.0",
            "description": "Backend for Speech-Battle mobile application",
            "endpoints": {
                "health": "/api/health",
                "auth": "/api/auth",
                "negotiations": "/api/negotiations",
                "admin": "/api/admin",
                "websocket": "/ws",
            }
        }

    @app.get("/api/health")
    def health():
        return {"status": "ok", "backend": "running"}

    return app


app = create_app()
