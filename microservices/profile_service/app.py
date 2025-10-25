from datetime import datetime
from pathlib import Path
from typing import Dict, List

from flask import Flask, jsonify, request
from flask_cors import CORS

import sqlite3


DATABASE_PATH = Path(__file__).with_name("profiles.db")
ALLOWED_AVAILABILITY = {"actively-looking", "exploring"}


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create storage for collaborator profiles."""
    with get_conn() as conn:
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
        conn.commit()


def _serialize_profile(row: sqlite3.Row, links: List[sqlite3.Row]) -> Dict:
    data = {
        "user_id": row["user_id"],
        "full_name": row["full_name"],
        "bio": row["bio"],
        "avatar_url": row["avatar_url"],
        "availability": row["availability"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
    data["links"] = [
        {"id": link["id"], "label": link["label"], "url": link["url"], "created_at": link["created_at"]}
        for link in links
    ]
    data["completeness"] = calculate_completeness(row, data["links"])
    return data


def calculate_completeness(profile_row: sqlite3.Row, links: List[Dict]) -> Dict:
    """Very lightweight scoring to communicate MVP value delivered."""
    sections = [
        ("full_name", bool(profile_row["full_name"])),
        ("bio", bool(profile_row["bio"])),
        ("avatar_url", bool(profile_row["avatar_url"])),
        ("links", len(links) > 0),
    ]
    score = sum(1 for _, filled in sections if filled)
    total = len(sections)
    percentage = int((score / total) * 100)
    return {"score": score, "total": total, "percentage": percentage}


def create_app() -> Flask:
    init_db()
    app = Flask(__name__)
    CORS(app)

    @app.get("/health")
    def health():
        return jsonify(status="ok", service="profile_service", timestamp=_now())

    @app.put("/profiles/<int:user_id>")
    def upsert_profile(user_id: int):
        payload = request.get_json(silent=True) or {}
        full_name = (payload.get("full_name") or "").strip()
        bio = (payload.get("bio") or "").strip() or None
        avatar_url = (payload.get("avatar_url") or "").strip() or None
        availability = (payload.get("availability") or "exploring").strip()

        if not full_name:
            return jsonify(error="full_name é obrigatório"), 400
        if availability not in ALLOWED_AVAILABILITY:
            return jsonify(error="availability deve ser 'actively-looking' ou 'exploring'"), 400

        timestamp = _now()
        with get_conn() as conn:
            existing = conn.execute(
                "SELECT user_id FROM profiles WHERE user_id = ?", (user_id,)
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE profiles
                    SET full_name = ?, bio = ?, avatar_url = ?, availability = ?, updated_at = ?
                    WHERE user_id = ?
                    """,
                    (full_name, bio, avatar_url, availability, timestamp, user_id),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO profiles (user_id, full_name, bio, avatar_url, availability, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, full_name, bio, avatar_url, availability, timestamp, timestamp),
                )
            conn.commit()

        return get_profile(user_id)

    @app.get("/profiles/<int:user_id>")
    def get_profile(user_id: int):
        with get_conn() as conn:
            profile = conn.execute(
                "SELECT * FROM profiles WHERE user_id = ?", (user_id,)
            ).fetchone()
            if not profile:
                return jsonify(error="perfil não encontrado"), 404
            links = conn.execute(
                "SELECT * FROM profile_links WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
            ).fetchall()

        data = _serialize_profile(profile, links)
        return jsonify(profile=data)

    @app.post("/profiles/<int:user_id>/links")
    def add_link(user_id: int):
        payload = request.get_json(silent=True) or {}
        label = (payload.get("label") or "").strip()
        url = (payload.get("url") or "").strip()

        if not label or not url:
            return jsonify(error="label e url são obrigatórios"), 400

        with get_conn() as conn:
            profile = conn.execute(
                "SELECT user_id FROM profiles WHERE user_id = ?", (user_id,)
            ).fetchone()
            if not profile:
                return jsonify(error="perfil não encontrado"), 404
            conn.execute(
                """
                INSERT INTO profile_links (user_id, label, url, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, label, url, _now()),
            )
            conn.commit()

        return get_profile(user_id)

    @app.delete("/profiles/<int:user_id>/links/<int:link_id>")
    def remove_link(user_id: int, link_id: int):
        with get_conn() as conn:
            deleted = conn.execute(
                "DELETE FROM profile_links WHERE id = ? AND user_id = ?", (link_id, user_id)
            )
            if deleted.rowcount == 0:
                return jsonify(error="link não encontrado"), 404
            conn.commit()
        return jsonify(message="link removido", profile_url=f"/profiles/{user_id}")

    @app.get("/profiles/<int:user_id>/completeness")
    def profile_completeness(user_id: int):
        with get_conn() as conn:
            profile = conn.execute(
                "SELECT * FROM profiles WHERE user_id = ?", (user_id,)
            ).fetchone()
            if not profile:
                return jsonify(error="perfil não encontrado"), 404
            links = conn.execute(
                "SELECT * FROM profile_links WHERE user_id = ?", (user_id,)
            ).fetchall()

        return jsonify(completeness=calculate_completeness(profile, links))

    @app.get("/metrics")
    def metrics():
        with get_conn() as conn:
            total_profiles = conn.execute("SELECT COUNT(*) AS count FROM profiles").fetchone()["count"]
            availability_breakdown = conn.execute(
                """
                SELECT availability, COUNT(*) AS total
                FROM profiles
                GROUP BY availability
                """
            ).fetchall()
            avg_links = conn.execute(
                """
                SELECT AVG(link_count) AS average
                FROM (
                    SELECT COUNT(*) AS link_count
                    FROM profile_links
                    GROUP BY user_id
                )
                """
            ).fetchone()

        availability = {row["availability"]: row["total"] for row in availability_breakdown}
        average_links = round(avg_links["average"], 2) if avg_links["average"] is not None else 0.0
        return jsonify(
            profiles={"total": total_profiles, "availability": availability},
            links={"average_per_profile": average_links},
            generated_at=_now(),
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5002, debug=True)
