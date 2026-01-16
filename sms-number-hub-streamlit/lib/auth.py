from __future__ import annotations

import os
from typing import Any

from passlib.context import CryptContext

from lib.db import create_user, get_user_by_username, init_db, log_event, set_last_login


_pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")

JWT_SECRET=4ZLLHrpUTb0Bm6I7ffhHRYdFMzjHvwL7KJdWJ_YKz0A
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=720

# ---- Backend ----
DATABASE_URL=sqlite:///./data/app.db
ENFORCE_TWILIO_SIGNATURE=true
TWILIO_AUTH_TOKEN=bad654727fb4fe072b957622e98cd5ce
OTP_VISIBILITY_MINUTES=10

# Bootstrap initial admin on first backend start
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123!CHANGE-ME
ADMIN_EMAIL=

# Optional: if you want Streamlit to know where the API is
API_BASE_URL=http://127.0.0.1:8000
def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def ensure_bootstrap_admin() -> None:
    init_db()

    admin_username = ADMIN_USERNAME
    admin_password = ADMIN_PASSWORD

    existing = get_user_by_username(admin_username)
    if existing is not None:
        return

    if not admin_password:
        log_event(
            level="warning",
            event_type="bootstrap_admin",
            message="No admin user exists and ADMIN_PASSWORD is not set; admin bootstrap skipped.",
            context={"username": admin_username},
        )
        return

    create_user(
        username=admin_username,
        email=os.getenv("ADMIN_EMAIL"),
        role="admin",
        password_hash=hash_password(admin_password),
    )
    log_event(
        level="info",
        event_type="bootstrap_admin",
        message="Bootstrapped initial admin user.",
        context={"username": admin_username},
    )


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    init_db()

    u = get_user_by_username(username)
    if not u:
        return None
    if not int(u.get("is_active") or 0):
        return None

    if not verify_password(password, str(u.get("password_hash") or "")):
        return None

    set_last_login(int(u["id"]))
    return u
