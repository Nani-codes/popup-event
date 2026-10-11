"""SQLite persistence for live signed-in guests."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "cafe.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              sub TEXT PRIMARY KEY,
              email TEXT NOT NULL,
              name TEXT,
              picture TEXT,
              interests TEXT DEFAULT '[]',
              prefs TEXT DEFAULT '{}',
              opt_in_match INTEGER DEFAULT 1,
              created_at REAL NOT NULL,
              last_seen REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
              order_id TEXT PRIMARY KEY,
              user_sub TEXT NOT NULL,
              guest_name TEXT,
              items_json TEXT NOT NULL,
              mods TEXT,
              eta_minutes INTEGER,
              status TEXT NOT NULL,
              created_at REAL NOT NULL,
              FOREIGN KEY (user_sub) REFERENCES users(sub)
            );

            CREATE TABLE IF NOT EXISTS oauth_tokens (
              user_sub TEXT NOT NULL,
              provider TEXT NOT NULL,
              access_token TEXT NOT NULL,
              refresh_token TEXT,
              expires_at REAL,
              scope TEXT,
              raw_json TEXT,
              updated_at REAL NOT NULL,
              PRIMARY KEY (user_sub, provider)
            );

            CREATE TABLE IF NOT EXISTS vibe_matches (
              user_sub TEXT NOT NULL,
              matched_sub TEXT NOT NULL,
              shared_json TEXT NOT NULL DEFAULT '[]',
              score INTEGER DEFAULT 0,
              notified INTEGER DEFAULT 0,
              created_at REAL NOT NULL,
              updated_at REAL NOT NULL,
              PRIMARY KEY (user_sub, matched_sub),
              FOREIGN KEY (user_sub) REFERENCES users(sub),
              FOREIGN KEY (matched_sub) REFERENCES users(sub)
            );

            CREATE TABLE IF NOT EXISTS match_notifications (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              to_sub TEXT NOT NULL,
              from_sub TEXT NOT NULL,
              message TEXT NOT NULL,
              read INTEGER DEFAULT 0,
              created_at REAL NOT NULL,
              FOREIGN KEY (to_sub) REFERENCES users(sub),
              FOREIGN KEY (from_sub) REFERENCES users(sub)
            );
            """
        )


def upsert_user(
    *, sub: str, email: str, name: str | None, picture: str | None
) -> tuple[dict, bool]:
    """Insert or update a guest. Returns (user, created)."""
    now = time.time()
    created = False
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE sub = ?", (sub,)).fetchone()
        if row:
            conn.execute(
                """
                UPDATE users
                SET email = ?, name = ?, picture = ?, last_seen = ?
                WHERE sub = ?
                """,
                (email, name, picture, now, sub),
            )
        else:
            created = True
            conn.execute(
                """
                INSERT INTO users (sub, email, name, picture, interests, prefs, opt_in_match, created_at, last_seen)
                VALUES (?, ?, ?, ?, '[]', '{}', 1, ?, ?)
                """,
                (sub, email, name, picture, now, now),
            )
    user = get_user(sub)
    assert user is not None
    return user, created


def get_user(sub: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE sub = ?", (sub,)).fetchone()
        if not row:
            return None
        return _user_from_row(row)


def update_profile(
    sub: str,
    *,
    interests: list[str] | None = None,
    prefs: dict[str, Any] | None = None,
    opt_in_match: bool | None = None,
) -> dict | None:
    user = get_user(sub)
    if not user:
        return None
    new_interests = interests if interests is not None else user["interests"]
    new_prefs = prefs if prefs is not None else user["prefs"]
    new_opt = (
        int(opt_in_match)
        if opt_in_match is not None
        else int(user["opt_in_match"])
    )
    with _connect() as conn:
        conn.execute(
            """
            UPDATE users
            SET interests = ?, prefs = ?, opt_in_match = ?, last_seen = ?
            WHERE sub = ?
            """,
            (json.dumps(new_interests), json.dumps(new_prefs), new_opt, time.time(), sub),
        )
    return get_user(sub)


def save_order(
    *,
    order_id: str,
    user_sub: str,
    guest_name: str,
    items: list[dict],
    mods: str,
    eta_minutes: int,
    status: str = "queued",
) -> dict:
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO orders
            (order_id, user_sub, guest_name, items_json, mods, eta_minutes, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                user_sub,
                guest_name,
                json.dumps(items),
                mods,
                eta_minutes,
                status,
                time.time(),
            ),
        )
    return get_order(order_id)  # type: ignore[return-value]


def get_order(order_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()
        if not row:
            return None
        return {
            "order_id": row["order_id"],
            "user_sub": row["user_sub"],
            "guest_name": row["guest_name"],
            "items": json.loads(row["items_json"]),
            "mods": row["mods"] or "",
            "eta_minutes": row["eta_minutes"],
            "status": row["status"],
            "created_at": row["created_at"],
        }


def list_orders_for_user(sub: str, limit: int = 10) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM orders WHERE user_sub = ?
            ORDER BY created_at DESC LIMIT ?
            """,
            (sub, limit),
        ).fetchall()
    return [
        {
            "order_id": r["order_id"],
            "guest_name": r["guest_name"],
            "items": json.loads(r["items_json"]),
            "mods": r["mods"] or "",
            "eta_minutes": r["eta_minutes"],
            "status": r["status"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def open_order_count() -> int:
    with _connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM orders WHERE status IN ('queued', 'making')"
        ).fetchone()
        return int(row["c"] if row else 0)


def find_matches(interests: list[str], exclude_sub: str = "") -> list[dict]:
    wanted = {i.strip().lower() for i in interests if i and i.strip()}
    if not wanted:
        return []
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM users WHERE opt_in_match = 1 AND sub != ?",
            (exclude_sub,),
        ).fetchall()
    scored: list[tuple[int, dict]] = []
    for row in rows:
        user = _user_from_row(row)
        their_tags = {t.lower() for t in user["interests"]}
        personality = (user.get("prefs") or {}).get("personality") or {}
        their_tags |= {t.lower() for t in (personality.get("tags") or [])}
        if personality.get("label"):
            their_tags.add(str(personality["label"]).lower())
        if personality.get("archetype"):
            their_tags.add(str(personality["archetype"]).lower())
        overlap = wanted & their_tags
        if overlap:
            scored.append(
                (
                    len(overlap),
                    {
                        **user,
                        "shared": sorted(overlap),
                        "personality_label": personality.get("label"),
                    },
                )
            )
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [u for _, u in scored[:5]]


def _user_from_row(row: sqlite3.Row) -> dict:
    return {
        "sub": row["sub"],
        "email": row["email"],
        "name": row["name"],
        "picture": row["picture"],
        "interests": json.loads(row["interests"] or "[]"),
        "prefs": json.loads(row["prefs"] or "{}"),
        "opt_in_match": bool(row["opt_in_match"]),
        "created_at": row["created_at"],
        "last_seen": row["last_seen"],
    }


def upsert_oauth_token(
    *,
    user_sub: str,
    provider: str,
    access_token: str,
    refresh_token: str | None = None,
    expires_at: float | None = None,
    scope: str | None = None,
    raw: dict | None = None,
) -> None:
    now = time.time()
    with _connect() as conn:
        existing = conn.execute(
            "SELECT refresh_token FROM oauth_tokens WHERE user_sub = ? AND provider = ?",
            (user_sub, provider),
        ).fetchone()
        keep_refresh = refresh_token or (existing["refresh_token"] if existing else None)
        conn.execute(
            """
            INSERT INTO oauth_tokens (
              user_sub, provider, access_token, refresh_token, expires_at, scope, raw_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_sub, provider) DO UPDATE SET
              access_token = excluded.access_token,
              refresh_token = COALESCE(excluded.refresh_token, oauth_tokens.refresh_token),
              expires_at = excluded.expires_at,
              scope = excluded.scope,
              raw_json = excluded.raw_json,
              updated_at = excluded.updated_at
            """,
            (
                user_sub,
                provider,
                access_token,
                keep_refresh,
                expires_at,
                scope,
                json.dumps(raw or {}),
                now,
            ),
        )


def get_oauth_token(user_sub: str, provider: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM oauth_tokens WHERE user_sub = ? AND provider = ?",
            (user_sub, provider),
        ).fetchone()
    if not row:
        return None
    return {
        "user_sub": row["user_sub"],
        "provider": row["provider"],
        "access_token": row["access_token"],
        "refresh_token": row["refresh_token"],
        "expires_at": row["expires_at"],
        "scope": row["scope"],
        "raw": json.loads(row["raw_json"] or "{}"),
        "updated_at": row["updated_at"],
    }


def delete_oauth_token(user_sub: str, provider: str) -> None:
    with _connect() as conn:
        conn.execute(
            "DELETE FROM oauth_tokens WHERE user_sub = ? AND provider = ?",
            (user_sub, provider),
        )


def upsert_vibe_match(
    *,
    user_sub: str,
    matched_sub: str,
    shared: list[str],
    score: int,
) -> None:
    now = time.time()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO vibe_matches (
              user_sub, matched_sub, shared_json, score, notified, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 0, ?, ?)
            ON CONFLICT(user_sub, matched_sub) DO UPDATE SET
              shared_json = excluded.shared_json,
              score = excluded.score,
              updated_at = excluded.updated_at
            """,
            (user_sub, matched_sub, json.dumps(shared), score, now, now),
        )


def list_vibe_matches(user_sub: str, limit: int = 20) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT m.*, u.name, u.email, u.picture, u.interests, u.prefs
            FROM vibe_matches m
            JOIN users u ON u.sub = m.matched_sub
            WHERE m.user_sub = ?
            ORDER BY m.score DESC, m.updated_at DESC
            LIMIT ?
            """,
            (user_sub, limit),
        ).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        prefs = json.loads(row["prefs"] or "{}")
        personality = prefs.get("personality") or {}
        out.append(
            {
                "matched_sub": row["matched_sub"],
                "handle": row["name"] or (row["email"] or "Guest").split("@")[0],
                "email": row["email"],
                "picture": row["picture"],
                "interests": json.loads(row["interests"] or "[]"),
                "personality": personality.get("label"),
                "shared": json.loads(row["shared_json"] or "[]"),
                "score": row["score"],
                "notified": bool(row["notified"]),
                "updated_at": row["updated_at"],
            }
        )
    return out


def mark_match_notified(user_sub: str, matched_sub: str) -> None:
    with _connect() as conn:
        conn.execute(
            """
            UPDATE vibe_matches SET notified = 1, updated_at = ?
            WHERE user_sub = ? AND matched_sub = ?
            """,
            (time.time(), user_sub, matched_sub),
        )


def create_match_notification(
    *, to_sub: str, from_sub: str, message: str
) -> dict[str, Any]:
    now = time.time()
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO match_notifications (to_sub, from_sub, message, read, created_at)
            VALUES (?, ?, ?, 0, ?)
            """,
            (to_sub, from_sub, message, now),
        )
        nid = int(cur.lastrowid)
    return {
        "id": nid,
        "to_sub": to_sub,
        "from_sub": from_sub,
        "message": message,
        "read": False,
        "created_at": now,
    }


def list_unread_notifications(to_sub: str, limit: int = 10) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT n.*, u.name, u.email, u.picture, u.prefs
            FROM match_notifications n
            JOIN users u ON u.sub = n.from_sub
            WHERE n.to_sub = ? AND n.read = 0
            ORDER BY n.created_at DESC
            LIMIT ?
            """,
            (to_sub, limit),
        ).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        prefs = json.loads(row["prefs"] or "{}")
        personality = prefs.get("personality") or {}
        out.append(
            {
                "id": row["id"],
                "from_sub": row["from_sub"],
                "from_handle": row["name"]
                or (row["email"] or "Guest").split("@")[0],
                "from_picture": row["picture"],
                "from_personality": personality.get("label"),
                "message": row["message"],
                "created_at": row["created_at"],
            }
        )
    return out


def mark_notifications_read(to_sub: str, ids: list[int]) -> None:
    if not ids:
        return
    placeholders = ",".join("?" for _ in ids)
    with _connect() as conn:
        conn.execute(
            f"""
            UPDATE match_notifications
            SET read = 1
            WHERE to_sub = ? AND id IN ({placeholders})
            """,
            (to_sub, *ids),
        )
