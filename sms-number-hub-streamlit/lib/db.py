from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                email TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS numbers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                e164 TEXT NOT NULL UNIQUE,
                provider TEXT,
                country TEXT,
                capabilities TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                notes TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS store_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                store_name TEXT,
                store_id TEXT,
                login_email TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(platform, store_id, login_email)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                number_id INTEGER NOT NULL,
                store_account_id INTEGER NOT NULL,
                purpose TEXT NOT NULL DEFAULT '2fa',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY(person_id) REFERENCES people(id),
                FOREIGN KEY(number_id) REFERENCES numbers(id),
                FOREIGN KEY(store_account_id) REFERENCES store_accounts(id),
                UNIQUE(number_id, store_account_id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT,
                role TEXT NOT NULL DEFAULT 'user',
                password_hash TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                last_login_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_phone_numbers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                number_id INTEGER NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(number_id) REFERENCES numbers(id) ON DELETE CASCADE,
                UNIQUE(user_id, number_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS phone_number_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number_id INTEGER NOT NULL,
                store_tag TEXT,
                purpose_tag TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(number_id) REFERENCES numbers(id) ON DELETE CASCADE,
                UNIQUE(number_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sms_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                provider_message_sid TEXT,
                to_number TEXT NOT NULL,
                from_number TEXT,
                body TEXT,
                received_at TEXT NOT NULL,
                number_id INTEGER,
                is_read INTEGER NOT NULL DEFAULT 0,
                otp_code TEXT,
                raw_payload TEXT,
                FOREIGN KEY(number_id) REFERENCES numbers(id) ON DELETE SET NULL,
                UNIQUE(provider, provider_message_sid)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                context_json TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        conn.execute("CREATE INDEX IF NOT EXISTS idx_sms_received_at ON sms_messages(received_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sms_to_number ON sms_messages(to_number)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sms_number_id ON sms_messages(number_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_numbers_user_id ON user_phone_numbers(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_numbers_number_id ON user_phone_numbers(number_id)")
        conn.commit()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_all(query: str, params: Iterable[Any] | None = None) -> list[dict[str, Any]]:
    with _connect() as conn:
        cur = conn.execute(query, tuple(params or ()))
        rows = cur.fetchall()
        return [dict(r) for r in rows]


def execute(query: str, params: Iterable[Any] | None = None) -> int:
    with _connect() as conn:
        cur = conn.execute(query, tuple(params or ()))
        conn.commit()
        return int(cur.lastrowid or 0)


def add_person(name: str, email: str | None) -> int:
    return execute(
        "INSERT INTO people (name, email, created_at) VALUES (?, ?, ?)",
        (name.strip(), (email or "").strip() or None, _now_iso()),
    )


def add_number(
    e164: str,
    provider: str | None,
    country: str | None,
    capabilities: str | None,
    status: str,
    notes: str | None,
) -> int:
    return execute(
        """
        INSERT INTO numbers (e164, provider, country, capabilities, status, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            e164.strip(),
            (provider or "").strip() or None,
            (country or "").strip() or None,
            (capabilities or "").strip() or None,
            status.strip(),
            (notes or "").strip() or None,
            _now_iso(),
        ),
    )


def add_store_account(
    platform: str,
    store_name: str | None,
    store_id: str | None,
    login_email: str | None,
    notes: str | None,
) -> int:
    return execute(
        """
        INSERT INTO store_accounts (platform, store_name, store_id, login_email, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            platform.strip(),
            (store_name or "").strip() or None,
            (store_id or "").strip() or None,
            (login_email or "").strip() or None,
            (notes or "").strip() or None,
            _now_iso(),
        ),
    )


def add_assignment(
    person_id: int,
    number_id: int,
    store_account_id: int,
    purpose: str,
) -> int:
    return execute(
        """
        INSERT INTO assignments (person_id, number_id, store_account_id, purpose, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (int(person_id), int(number_id), int(store_account_id), purpose.strip(), _now_iso()),
    )


def deactivate_assignment(assignment_id: int) -> None:
    execute("UPDATE assignments SET is_active = 0 WHERE id = ?", (int(assignment_id),))


def delete_row(table: str, row_id: int) -> None:
    if table not in {
        "people",
        "numbers",
        "store_accounts",
        "assignments",
        "users",
        "user_phone_numbers",
        "phone_number_tags",
        "sms_messages",
        "app_events",
    }:
        raise ValueError("Invalid table")
    execute(f"DELETE FROM {table} WHERE id = ?", (int(row_id),))


def get_people() -> list[dict[str, Any]]:
    return fetch_all("SELECT * FROM people ORDER BY name")


def get_numbers() -> list[dict[str, Any]]:
    return fetch_all("SELECT * FROM numbers ORDER BY e164")


def get_store_accounts() -> list[dict[str, Any]]:
    return fetch_all(
        "SELECT * FROM store_accounts ORDER BY platform, COALESCE(store_name, ''), COALESCE(store_id, '')"
    )


def get_assignments(active_only: bool = True) -> list[dict[str, Any]]:
    where = "WHERE a.is_active = 1" if active_only else ""
    return fetch_all(
        f"""
        SELECT
            a.id,
            a.purpose,
            a.is_active,
            a.created_at,
            p.name AS person_name,
            p.email AS person_email,
            n.e164 AS number_e164,
            n.provider AS number_provider,
            s.platform AS platform,
            s.store_name AS store_name,
            s.store_id AS store_id,
            s.login_email AS login_email
        FROM assignments a
        JOIN people p ON p.id = a.person_id
        JOIN numbers n ON n.id = a.number_id
        JOIN store_accounts s ON s.id = a.store_account_id
        {where}
        ORDER BY a.is_active DESC, p.name, s.platform
        """
    )


def export_all() -> dict[str, list[dict[str, Any]]]:
    return {
        "people": get_people(),
        "numbers": get_numbers(),
        "store_accounts": get_store_accounts(),
        "assignments": fetch_all("SELECT * FROM assignments ORDER BY id"),
    }


def import_table(table: str, rows: list[dict[str, Any]]) -> None:
    if table not in {
        "people",
        "numbers",
        "store_accounts",
        "assignments",
        "users",
        "user_phone_numbers",
        "phone_number_tags",
        "sms_messages",
    }:
        raise ValueError("Invalid table")

    with _connect() as conn:
        if table == "people":
            conn.executemany(
                "INSERT OR IGNORE INTO people (id, name, email, created_at) VALUES (?, ?, ?, ?)",
                [
                    (
                        r.get("id"),
                        r.get("name"),
                        r.get("email"),
                        r.get("created_at") or _now_iso(),
                    )
                    for r in rows
                ],
            )
        elif table == "numbers":
            conn.executemany(
                """
                INSERT OR IGNORE INTO numbers (id, e164, provider, country, capabilities, status, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        r.get("id"),
                        r.get("e164"),
                        r.get("provider"),
                        r.get("country"),
                        r.get("capabilities"),
                        r.get("status") or "active",
                        r.get("notes"),
                        r.get("created_at") or _now_iso(),
                    )
                    for r in rows
                ],
            )
        elif table == "store_accounts":
            conn.executemany(
                """
                INSERT OR IGNORE INTO store_accounts (id, platform, store_name, store_id, login_email, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        r.get("id"),
                        r.get("platform"),
                        r.get("store_name"),
                        r.get("store_id"),
                        r.get("login_email"),
                        r.get("notes"),
                        r.get("created_at") or _now_iso(),
                    )
                    for r in rows
                ],
            )
        else:
            conn.executemany(
                """
                INSERT OR IGNORE INTO assignments
                    (id, person_id, number_id, store_account_id, purpose, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        r.get("id"),
                        r.get("person_id"),
                        r.get("number_id"),
                        r.get("store_account_id"),
                        r.get("purpose") or "2fa",
                        r.get("is_active") if r.get("is_active") is not None else 1,
                        r.get("created_at") or _now_iso(),
                    )
                    for r in rows
                ],
            )

        conn.commit()


def log_event(level: str, event_type: str, message: str, context: dict[str, Any] | None = None) -> int:
    return execute(
        """
        INSERT INTO app_events (level, event_type, message, context_json, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            level.strip().lower(),
            event_type.strip(),
            message,
            json.dumps(context or {}, ensure_ascii=False),
            _now_iso(),
        ),
    )


def get_events(limit: int = 200) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 2000))
    return fetch_all("SELECT * FROM app_events ORDER BY id DESC LIMIT ?", (limit,))


def create_user(username: str, email: str | None, role: str, password_hash: str) -> int:
    return execute(
        """
        INSERT INTO users (username, email, role, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            username.strip().lower(),
            (email or "").strip() or None,
            role.strip().lower(),
            password_hash,
            _now_iso(),
        ),
    )


def get_user_by_username(username: str) -> dict[str, Any] | None:
    rows = fetch_all(
        "SELECT * FROM users WHERE username = ? LIMIT 1", (username.strip().lower(),)
    )
    return rows[0] if rows else None


def get_user(user_id: int) -> dict[str, Any] | None:
    rows = fetch_all("SELECT * FROM users WHERE id = ? LIMIT 1", (int(user_id),))
    return rows[0] if rows else None


def list_users(active_only: bool = True) -> list[dict[str, Any]]:
    where = "WHERE is_active = 1" if active_only else ""
    return fetch_all(f"SELECT * FROM users {where} ORDER BY username")


def set_user_active(user_id: int, is_active: bool) -> None:
    execute("UPDATE users SET is_active = ? WHERE id = ?", (1 if is_active else 0, int(user_id)))


def set_last_login(user_id: int) -> None:
    execute("UPDATE users SET last_login_at = ? WHERE id = ?", (_now_iso(), int(user_id)))


def assign_number_to_user(user_id: int, number_id: int) -> int:
    return execute(
        """
        INSERT INTO user_phone_numbers (user_id, number_id, created_at)
        VALUES (?, ?, ?)
        """,
        (int(user_id), int(number_id), _now_iso()),
    )


def unassign_number_from_user(user_id: int, number_id: int) -> None:
    execute(
        "UPDATE user_phone_numbers SET is_active = 0 WHERE user_id = ? AND number_id = ?",
        (int(user_id), int(number_id)),
    )


def get_user_numbers(user_id: int, active_only: bool = True) -> list[dict[str, Any]]:
    where = "AND upn.is_active = 1" if active_only else ""
    return fetch_all(
        f"""
        SELECT
            n.*, upn.is_active AS user_is_active,
            t.store_tag AS store_tag,
            t.purpose_tag AS purpose_tag
        FROM user_phone_numbers upn
        JOIN numbers n ON n.id = upn.number_id
        LEFT JOIN phone_number_tags t ON t.number_id = n.id
        WHERE upn.user_id = ?
        {where}
        ORDER BY n.e164
        """,
        (int(user_id),),
    )


def get_number_users(number_id: int, active_only: bool = True) -> list[dict[str, Any]]:
    where = "AND upn.is_active = 1" if active_only else ""
    return fetch_all(
        f"""
        SELECT u.id AS user_id, u.username, u.email, u.role, upn.is_active, upn.created_at
        FROM user_phone_numbers upn
        JOIN users u ON u.id = upn.user_id
        WHERE upn.number_id = ?
        {where}
        ORDER BY u.username
        """,
        (int(number_id),),
    )


def set_number_tags(number_id: int, store_tag: str | None, purpose_tag: str | None) -> None:
    execute(
        """
        INSERT INTO phone_number_tags (number_id, store_tag, purpose_tag, created_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(number_id) DO UPDATE SET
            store_tag = excluded.store_tag,
            purpose_tag = excluded.purpose_tag
        """,
        (
            int(number_id),
            (store_tag or "").strip() or None,
            (purpose_tag or "").strip() or None,
            _now_iso(),
        ),
    )


def _extract_otp_code(body: str | None) -> str | None:
    if not body:
        return None
    m = re.search(r"\b(\d{4,8})\b", body)
    return m.group(1) if m else None


def upsert_sms_message(
    *,
    provider: str,
    provider_message_sid: str | None,
    to_number: str,
    from_number: str | None,
    body: str | None,
    received_at: str | None,
    raw_payload: dict[str, Any] | None,
) -> int:
    to_number_clean = to_number.strip()
    number_rows = fetch_all("SELECT id FROM numbers WHERE e164 = ? LIMIT 1", (to_number_clean,))
    number_id = int(number_rows[0]["id"]) if number_rows else None
    otp = _extract_otp_code(body)
    try:
        return execute(
            """
            INSERT INTO sms_messages
                (provider, provider_message_sid, to_number, from_number, body, received_at, number_id, otp_code, raw_payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                provider.strip().lower(),
                provider_message_sid,
                to_number_clean,
                (from_number or "").strip() or None,
                body,
                received_at or _now_iso(),
                number_id,
                otp,
                json.dumps(raw_payload or {}, ensure_ascii=False),
            ),
        )
    except sqlite3.IntegrityError:
        if provider_message_sid:
            rows = fetch_all(
                """
                SELECT id FROM sms_messages
                WHERE provider = ? AND provider_message_sid = ?
                LIMIT 1
                """,
                (provider.strip().lower(), provider_message_sid),
            )
            if rows:
                return int(rows[0]["id"])
        raise


def mark_sms_read(message_id: int, is_read: bool = True) -> None:
    execute("UPDATE sms_messages SET is_read = ? WHERE id = ?", (1 if is_read else 0, int(message_id)))


def query_sms_messages(
    *,
    viewer_user_id: int | None,
    viewer_role: str | None,
    assigned_only: bool,
    to_number: str | None = None,
    from_number: str | None = None,
    store_tag: str | None = None,
    purpose_tag: str | None = None,
    unread_only: bool = False,
    since_iso: str | None = None,
    until_iso: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 5000))
    params: list[Any] = []
    where: list[str] = []
    join_user_numbers = ""

    if assigned_only and (viewer_role or "").lower() != "admin":
        if viewer_user_id is None:
            return []
        join_user_numbers = "JOIN user_phone_numbers upn ON upn.number_id = n.id AND upn.user_id = ? AND upn.is_active = 1"
        params.append(int(viewer_user_id))

    if to_number:
        where.append("m.to_number = ?")
        params.append(to_number.strip())
    if from_number:
        where.append("m.from_number = ?")
        params.append(from_number.strip())
    if unread_only:
        where.append("m.is_read = 0")
    if since_iso:
        where.append("m.received_at >= ?")
        params.append(since_iso)
    if until_iso:
        where.append("m.received_at <= ?")
        params.append(until_iso)
    if store_tag:
        where.append("t.store_tag = ?")
        params.append(store_tag.strip())
    if purpose_tag:
        where.append("t.purpose_tag = ?")
        params.append(purpose_tag.strip())

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    return fetch_all(
        f"""
        SELECT
            m.id,
            m.provider,
            m.provider_message_sid,
            m.to_number,
            m.from_number,
            m.body,
            m.received_at,
            m.is_read,
            m.otp_code,
            n.id AS number_id,
            n.e164 AS number_e164,
            t.store_tag AS store_tag,
            t.purpose_tag AS purpose_tag
        FROM sms_messages m
        LEFT JOIN numbers n ON n.id = m.number_id
        LEFT JOIN phone_number_tags t ON t.number_id = n.id
        {join_user_numbers}
        {where_sql}
        ORDER BY m.received_at DESC
        LIMIT {limit}
        """,
        params,
    )


def get_dashboard_stats(viewer_user_id: int | None, viewer_role: str | None) -> dict[str, Any]:
    assigned_only = (viewer_role or "").lower() != "admin"
    base_params: list[Any] = []
    join_user_numbers = ""
    if assigned_only:
        if viewer_user_id is None:
            return {
                "active_phone_numbers": 0,
                "sms_today": 0,
                "otp_today": 0,
                "unread": 0,
            }
        join_user_numbers = "JOIN user_phone_numbers upn ON upn.number_id = n.id AND upn.user_id = ? AND upn.is_active = 1"
        base_params.append(int(viewer_user_id))

    today_prefix = datetime.now(timezone.utc).date().isoformat()

    active_numbers = fetch_all(
        f"""
        SELECT COUNT(DISTINCT n.id) AS c
        FROM numbers n
        {join_user_numbers}
        WHERE n.status = 'active'
        """,
        base_params,
    )
    sms_today = fetch_all(
        f"""
        SELECT COUNT(*) AS c
        FROM sms_messages m
        LEFT JOIN numbers n ON n.id = m.number_id
        {join_user_numbers}
        WHERE m.received_at LIKE ? || '%'
        """,
        [*base_params, today_prefix],
    )
    otp_today = fetch_all(
        f"""
        SELECT COUNT(*) AS c
        FROM sms_messages m
        LEFT JOIN numbers n ON n.id = m.number_id
        {join_user_numbers}
        WHERE m.received_at LIKE ? || '%' AND m.otp_code IS NOT NULL
        """,
        [*base_params, today_prefix],
    )
    unread = fetch_all(
        f"""
        SELECT COUNT(*) AS c
        FROM sms_messages m
        LEFT JOIN numbers n ON n.id = m.number_id
        {join_user_numbers}
        WHERE m.is_read = 0
        """,
        base_params,
    )
    return {
        "active_phone_numbers": int((active_numbers[0]["c"] if active_numbers else 0) or 0),
        "sms_today": int((sms_today[0]["c"] if sms_today else 0) or 0),
        "otp_today": int((otp_today[0]["c"] if otp_today else 0) or 0),
        "unread": int((unread[0]["c"] if unread else 0) or 0),
    }
