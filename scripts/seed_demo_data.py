from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict

from werkzeug.security import generate_password_hash


ROOT_DIR = Path(__file__).resolve().parent.parent
AUTH_DB = ROOT_DIR / "microservices" / "auth_service" / "auth.db"
PROFILE_DB = ROOT_DIR / "microservices" / "profile_service" / "profiles.db"
SKILLS_DB = ROOT_DIR / "microservices" / "skills_service" / "skills.db"
ANALYTICS_DB = ROOT_DIR / "microservices" / "analytics_service" / "analytics.db"


def _now() -> str:
    return datetime.now(tz=UTC).isoformat(timespec="seconds")


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def seed_auth() -> Dict[str, int]:
    path = AUTH_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS login_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                success INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        users = [
            {"email": "sofia.dev@example.com", "password": "colab123"},
            {"email": "mateus.ux@example.com", "password": "designer123"},
        ]

        email_to_id: Dict[str, int] = {}
        for user in users:
            conn.execute(
                """
                INSERT INTO users (email, password_hash, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET password_hash = excluded.password_hash
                """,
                (user["email"], generate_password_hash(user["password"]), _now()),
            )
            user_id = conn.execute(
                "SELECT id FROM users WHERE email = ?",
                (user["email"],),
            ).fetchone()["id"]
            email_to_id[user["email"]] = user_id

        existing_events = conn.execute("SELECT COUNT(*) AS total FROM login_events").fetchone()["total"]
        if existing_events == 0:
            for email, user_id in email_to_id.items():
                conn.execute(
                    "INSERT INTO login_events (user_id, success, created_at) VALUES (?, ?, ?)",
                    (user_id, 1, _now()),
                )
                conn.execute(
                    "INSERT INTO login_events (user_id, success, created_at) VALUES (?, ?, ?)",
                    (user_id, 0, _now()),
                )
        conn.commit()
    return email_to_id


def seed_profiles(email_to_id: Dict[str, int]) -> None:
    path = PROFILE_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                bio TEXT,
                avatar_url TEXT,
                availability TEXT NOT NULL DEFAULT 'exploring',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS profile_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                label TEXT NOT NULL,
                url TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES profiles (user_id)
            )
            """
        )

        profiles = {
            "sofia.dev@example.com": {
                "full_name": "Sofia Lima",
                "bio": "Desenvolvedora backend focada em Python e APIs resilientes.",
                "avatar_url": "https://avatars.githubusercontent.com/u/9919?s=200&v=4",
                "availability": "actively-looking",
                "links": [
                    {"label": "LinkedIn", "url": "https://www.linkedin.com/in/sofialima"},
                    {"label": "GitHub", "url": "https://github.com/sofia-dev"},
                ],
            },
            "mateus.ux@example.com": {
                "full_name": "Mateus Carvalho",
                "bio": "UX/UI designer com experiência em testes de usabilidade e prototipação.",
                "avatar_url": "https://images.unsplash.com/photo-1502685104226-ee32379fefbe?auto=format&fit=facearea&w=256&h=256",
                "availability": "exploring",
                "links": [
                    {"label": "Behance", "url": "https://www.behance.net/mateuscarvalho"},
                    {"label": "Portfólio", "url": "https://mateusux.me"},
                ],
            },
        }

        for email, data in profiles.items():
            user_id = email_to_id.get(email)
            if not user_id:
                continue
            timestamp = _now()
            conn.execute(
                """
                INSERT INTO profiles (user_id, full_name, bio, avatar_url, availability, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    full_name = excluded.full_name,
                    bio = excluded.bio,
                    avatar_url = excluded.avatar_url,
                    availability = excluded.availability,
                    updated_at = excluded.updated_at
                """,
                (
                    user_id,
                    data["full_name"],
                    data["bio"],
                    data["avatar_url"],
                    data["availability"],
                    timestamp,
                    timestamp,
                ),
            )
            conn.execute("DELETE FROM profile_links WHERE user_id = ?", (user_id,))
            for link in data["links"]:
                conn.execute(
                    """
                    INSERT INTO profile_links (user_id, label, url, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, link["label"], link["url"], _now()),
                )
        conn.commit()


def seed_skills(email_to_id: Dict[str, int]) -> None:
    path = SKILLS_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL DEFAULT 'approved',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                skill_id INTEGER NOT NULL,
                proficiency TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (skill_id) REFERENCES skills (id)
            )
            """
        )

        catalog = [
            {"name": "Python", "status": "approved"},
            {"name": "UX/UI Design", "status": "approved"},
            {"name": "Data Science", "status": "approved"},
            {"name": "Gestão de Projetos", "status": "approved"},
            {"name": "Modelo de Negócios Lean", "status": "pending"},
        ]

        for skill in catalog:
            conn.execute(
                """
                INSERT INTO skills (name, status, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET status = excluded.status
                """,
                (skill["name"], skill["status"], _now()),
            )

        user_profiles = {
            "sofia.dev@example.com": [
                {"skill": "Python", "proficiency": "advanced"},
                {"skill": "Data Science", "proficiency": "intermediate"},
            ],
            "mateus.ux@example.com": [
                {"skill": "UX/UI Design", "proficiency": "advanced"},
                {"skill": "Gestão de Projetos", "proficiency": "basic"},
                {"skill": "Pesquisa com Usuários", "proficiency": "intermediate"},
            ],
        }

        for email, skills in user_profiles.items():
            user_id = email_to_id.get(email)
            if not user_id:
                continue
            conn.execute("DELETE FROM user_skills WHERE user_id = ?", (user_id,))
            for entry in skills:
                skill_name = entry["skill"]
                skill_row = conn.execute(
                    "SELECT id FROM skills WHERE LOWER(name) = LOWER(?)",
                    (skill_name,),
                ).fetchone()
                if skill_row is None:
                    cursor = conn.execute(
                        "INSERT INTO skills (name, status, created_at) VALUES (?, 'pending', ?)",
                        (skill_name, _now()),
                    )
                    skill_id = cursor.lastrowid
                else:
                    skill_id = skill_row["id"]
                conn.execute(
                    """
                    INSERT INTO user_skills (user_id, skill_id, proficiency, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, skill_id, entry["proficiency"], _now()),
                )
        conn.commit()


def seed_analytics(email_to_id: Dict[str, int]) -> None:
    path = ANALYTICS_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                user_id INTEGER,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        existing = conn.execute("SELECT COUNT(*) AS total FROM events").fetchone()["total"]
        if existing > 0:
            return

        events = [
            {
                "event_type": "user.registered",
                "email": "sofia.dev@example.com",
                "payload": {"source": "seed_demo"},
            },
            {
                "event_type": "profile.completed",
                "email": "sofia.dev@example.com",
                "payload": {"completeness": 100},
            },
            {
                "event_type": "user.registered",
                "email": "mateus.ux@example.com",
                "payload": {"source": "seed_demo"},
            },
            {
                "event_type": "skill.added",
                "email": "mateus.ux@example.com",
                "payload": {"skill": "Pesquisa com Usuários"},
            },
            {
                "event_type": "project.viewed",
                "email": None,
                "payload": {"project_id": 101, "channel": "discover"},
            },
        ]

        for event in events:
            email = event["email"]
            user_id = email_to_id.get(email) if email else None
            conn.execute(
                """
                INSERT INTO events (event_type, user_id, payload, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (event["event_type"], user_id, json.dumps(event["payload"]), _now()),
            )
        conn.commit()


def main() -> None:
    print("Seeding demo data for MVP...")
    email_to_id = seed_auth()
    seed_profiles(email_to_id)
    seed_skills(email_to_id)
    seed_analytics(email_to_id)
    print("Demo data ready!")
    for email, user_id in email_to_id.items():
        print(f" - {email} (user_id={user_id})")


if __name__ == "__main__":
    main()
