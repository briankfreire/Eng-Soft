from datetime import datetime
from pathlib import Path
from typing import Dict

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

import sqlite3


DATABASE_PATH = Path(__file__).with_name("auth.db")


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database structures for the authentication service."""
    with get_conn() as conn:
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
        conn.commit()


def _serialize_user(row: sqlite3.Row) -> Dict:
    return {"id": row["id"], "email": row["email"], "created_at": row["created_at"]}


def create_app() -> Flask:
    """Factory that configures and returns the Flask app."""
    init_db()
    app = Flask(__name__)
    CORS(app)

    @app.get("/health")
    def health():
        return jsonify(status="ok", service="auth_service", timestamp=_now())

    @app.post("/register")
    def register():
        payload = request.get_json(silent=True) or {}
        email = (payload.get("email") or "").strip().lower()
        password = payload.get("password")

        if not email or not password:
            return jsonify(error="email e password são obrigatórios"), 400
        if len(password) < 6:
            return jsonify(error="password deve ter pelo menos 6 caracteres"), 400

        password_hash = generate_password_hash(password)
        try:
            with get_conn() as conn:
                cursor = conn.execute(
                    "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
                    (email, password_hash, _now()),
                )
                user_id = cursor.lastrowid
                conn.commit()
        except sqlite3.IntegrityError:
            return jsonify(error="email já cadastrado"), 409

        return jsonify(message="usuário criado", user={"id": user_id, "email": email}), 201

    @app.post("/login")
    def login():
        payload = request.get_json(silent=True) or {}
        email = (payload.get("email") or "").strip().lower()
        password = payload.get("password")

        if not email or not password:
            return jsonify(error="email e password são obrigatórios"), 400

        with get_conn() as conn:
            user = conn.execute(
                "SELECT id, email, password_hash, created_at FROM users WHERE email = ?",
                (email,),
            ).fetchone()

        if not user or not check_password_hash(user["password_hash"], password):
            _record_login_event(user_id=user["id"] if user else None, success=False)
            return jsonify(error="credenciais inválidas"), 401

        _record_login_event(user_id=user["id"], success=True)
        data = _serialize_user(user)
        return jsonify(message="login ok", user=data)

    def _record_login_event(user_id: int | None, success: bool) -> None:
        if user_id is None:
            return
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO login_events (user_id, success, created_at) VALUES (?, ?, ?)",
                (user_id, int(success), _now()),
            )
            conn.commit()

    @app.get("/users/<int:user_id>")
    def get_user(user_id: int):
        with get_conn() as conn:
            row = conn.execute(
                "SELECT id, email, created_at FROM users WHERE id = ?", (user_id,)
            ).fetchone()

        if not row:
            return jsonify(error="usuário não encontrado"), 404
        return jsonify(user=_serialize_user(row))

    @app.get("/metrics")
    def metrics():
        with get_conn() as conn:
            total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            login_totals = conn.execute(
                """
                SELECT
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failure_count
                FROM login_events
                """
            ).fetchone()

        success_count = login_totals["success_count"] or 0
        failure_count = login_totals["failure_count"] or 0
        return jsonify(
            users={"total": total_users},
            logins={"success": success_count, "failure": failure_count},
            generated_at=_now(),
        )

    return app


# Expose the WSGI application object at module level for gunicorn (app:app)
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
