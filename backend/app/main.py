from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from .config import FRONTEND_DIR, get_settings
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


def file_or_404(path: Path, media_type: str | None = None) -> FileResponse:
    if not path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")
    return FileResponse(path, media_type=media_type)


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

    pages_dir = FRONTEND_DIR / "pages"
    assets_dir = FRONTEND_DIR / "assets"
    js_dir = FRONTEND_DIR / "js"
    css_file = FRONTEND_DIR / "css" / "style.css"

    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    if js_dir.exists():
        app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    def page(name: str) -> FileResponse:
        return file_or_404(pages_dir / name, "text/html")

    @app.get("/")
    def root_page():
        # Не отдаём арену сразу: сначала gate проверяет сессию в localStorage
        return page("gate.html")

    @app.get("/gate.html")
    def gate_page():
        return page("gate.html")

    @app.get("/index.html")
    def index_page():
        return page("index.html")

    @app.get("/auth.html")
    def auth_page():
        return page("auth.html")

    @app.get("/registration.html")
    def registration_page():
        return page("registration.html")

    @app.get("/profile.html")
    def profile_page():
        return page("profile.html")

    @app.get("/history.html")
    def history_page():
        return page("history.html")

    @app.get("/admin.html")
    def admin_page():
        return page("admin.html")

    @app.get("/admin-users.html")
    def admin_users_page():
        return page("admin-users.html")

    @app.get("/admin-profile.html")
    def admin_profile_page():
        return page("admin-profile.html")

    @app.get("/style.css")
    def style_css():
        return file_or_404(css_file, "text/css")

    return app


app = create_app()
