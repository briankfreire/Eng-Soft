from datetime import datetime
from pathlib import Path
from typing import Dict, List

from flask import Flask, jsonify, request
from flask_cors import CORS

import sqlite3


DATABASE_PATH = Path(__file__).with_name("skills.db")
DEFAULT_SKILLS = ["Python", "UX/UI Design", "Gestão de Projetos", "Data Science"]
ALLOWED_PROFICIENCIES = {"basic", "intermediate", "advanced"}


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Prepare storage for skills and user proficiencies."""
    with get_conn() as conn:
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
        conn.commit()

        for skill_name in DEFAULT_SKILLS:
            conn.execute(
                "INSERT OR IGNORE INTO skills (name, status, created_at) VALUES (?, 'approved', ?)",
                (skill_name, _now()),
            )
        conn.commit()


def serialize_skill(row: sqlite3.Row) -> Dict:
    return {"id": row["id"], "name": row["name"], "status": row["status"], "created_at": row["created_at"]}


def serialize_user_skill(row: sqlite3.Row) -> Dict:
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "skill_id": row["skill_id"],
        "skill_name": row["skill_name"],
        "proficiency": row["proficiency"],
        "created_at": row["created_at"],
    }


def create_app() -> Flask:
    init_db()
    app = Flask(__name__)
    CORS(app)

    @app.get("/health")
    def health():
        return jsonify(status="ok", service="skills_service", timestamp=_now())

    @app.get("/skills")
    def list_skills():
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT id, name, status, created_at FROM skills ORDER BY name ASC"
            ).fetchall()
        return jsonify(skills=[serialize_skill(row) for row in rows])

    @app.post("/skills")
    def create_skill():
        payload = request.get_json(silent=True) or {}
        name = (payload.get("name") or "").strip()
        status = payload.get("status", "pending").strip()

        if not name:
            return jsonify(error="name é obrigatório"), 400
        if status not in {"pending", "approved"}:
            return jsonify(error="status inválido"), 400

        try:
            with get_conn() as conn:
                cursor = conn.execute(
                    "INSERT INTO skills (name, status, created_at) VALUES (?, ?, ?)",
                    (name, status, _now()),
                )
                conn.commit()
        except sqlite3.IntegrityError:
            return jsonify(error="skill já cadastrada"), 409

        with get_conn() as conn:
            created = conn.execute(
                "SELECT id, name, status, created_at FROM skills WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return jsonify(skill=serialize_skill(created)), 201

    @app.post("/users/<int:user_id>/skills")
    def add_user_skill(user_id: int):
        payload = request.get_json(silent=True) or {}
        skill_id = payload.get("skill_id")
        skill_name = (payload.get("skill_name") or "").strip()
        proficiency = (payload.get("proficiency") or "").strip().lower() or "basic"

        if skill_id is None and not skill_name:
            return jsonify(error="skill_id ou skill_name é obrigatório"), 400
        if proficiency not in ALLOWED_PROFICIENCIES:
            return jsonify(error="proficiency deve ser basic, intermediate ou advanced"), 400

        with get_conn() as conn:
            if skill_id is None:
                skill = conn.execute(
                    "SELECT id, name FROM skills WHERE LOWER(name) = LOWER(?)",
                    (skill_name,),
                ).fetchone()
                if not skill:
                    # Auto-cadastra sugestão pendente para cumprir MVP
                    cursor = conn.execute(
                        "INSERT INTO skills (name, status, created_at) VALUES (?, 'pending', ?)",
                        (skill_name, _now()),
                    )
                    skill_id = cursor.lastrowid
                else:
                    skill_id = skill["id"]

            conn.execute(
                """
                INSERT INTO user_skills (user_id, skill_id, proficiency, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, skill_id, proficiency, _now()),
            )
            conn.commit()

        return list_user_skills(user_id)

    @app.get("/users/<int:user_id>/skills")
    def list_user_skills(user_id: int):
        with get_conn() as conn:
            rows = conn.execute(
                """
                SELECT us.id, us.user_id, us.skill_id, us.proficiency, us.created_at, s.name AS skill_name
                FROM user_skills us
                JOIN skills s ON us.skill_id = s.id
                WHERE us.user_id = ?
                ORDER BY us.created_at DESC
                """,
                (user_id,),
            ).fetchall()
        return jsonify(user_id=user_id, skills=[serialize_user_skill(row) for row in rows])

    @app.delete("/users/<int:user_id>/skills/<int:user_skill_id>")
    def delete_user_skill(user_id: int, user_skill_id: int):
        with get_conn() as conn:
            deleted = conn.execute(
                "DELETE FROM user_skills WHERE id = ? AND user_id = ?", (user_skill_id, user_id)
            )
            if deleted.rowcount == 0:
                return jsonify(error="registro de habilidade não encontrado"), 404
            conn.commit()
        return jsonify(message="habilidade removida", user_id=user_id)

    @app.get("/metrics")
    def metrics():
        with get_conn() as conn:
            total_skills = conn.execute("SELECT COUNT(*) AS total FROM skills").fetchone()["total"]
            pending_skills = conn.execute(
                "SELECT COUNT(*) AS total FROM skills WHERE status = 'pending'"
            ).fetchone()["total"]
            distribution = conn.execute(
                """
                SELECT proficiency, COUNT(*) AS total
                FROM user_skills
                GROUP BY proficiency
                """
            ).fetchall()

        proficiencies = {row["proficiency"]: row["total"] for row in distribution}
        return jsonify(
            skills={"total": total_skills, "pending": pending_skills},
            proficiencies=proficiencies,
            generated_at=_now(),
        )

    return app


# Expose the WSGI application object at module level for gunicorn (app:app)
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
