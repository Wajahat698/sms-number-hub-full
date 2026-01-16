from __future__ import annotations

import os
from typing import Any

from passlib.context import CryptContext

from lib.db import create_user, get_user_by_username, init_db, log_event, set_last_login


_pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def ensure_bootstrap_admin() -> None:
    init_db()

    admin_username = (os.getenv("ADMIN_USERNAME") or "admin").strip().lower()
    admin_password = (os.getenv("ADMIN_PASSWORD") or "").strip()

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
