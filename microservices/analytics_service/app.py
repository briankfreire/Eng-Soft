import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from flask import Flask, jsonify, request
from flask_cors import CORS

import sqlite3


DATABASE_PATH = Path(__file__).with_name("analytics.db")


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create a lightweight event store."""
    with get_conn() as conn:
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
        conn.commit()


def serialize_event(row: sqlite3.Row) -> Dict:
    payload = row["payload"]
    parsed = json.loads(payload) if payload else {}
    return {
        "id": row["id"],
        "event_type": row["event_type"],
        "user_id": row["user_id"],
        "payload": parsed,
        "created_at": row["created_at"],
    }


def create_app() -> Flask:
    init_db()
    app = Flask(__name__)
    CORS(app)

    @app.get("/health")
    def health():
        return jsonify(status="ok", service="analytics_service", timestamp=_now())

    @app.post("/events")
    def record_event():
        payload = request.get_json(silent=True) or {}
        event_type = (payload.get("event_type") or "").strip()
        user_id = payload.get("user_id")
        event_payload = payload.get("payload", {})

        if not event_type:
            return jsonify(error="event_type é obrigatório"), 400
        if user_id is not None and not isinstance(user_id, int):
            return jsonify(error="user_id deve ser inteiro"), 400

        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO events (event_type, user_id, payload, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (event_type, user_id, json.dumps(event_payload), _now()),
            )
            conn.commit()

        return jsonify(message="evento registrado"), 201

    @app.get("/events/recent")
    def recent_events():
        limit = request.args.get("limit", default=10, type=int)
        limit = max(1, min(limit, 100))

        with get_conn() as conn:
            rows = conn.execute(
                """
                SELECT id, event_type, user_id, payload, created_at
                FROM events
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return jsonify(events=[serialize_event(row) for row in rows])

    @app.get("/metrics")
    def metrics():
        with get_conn() as conn:
            rows = conn.execute(
                """
                SELECT event_type, COUNT(*) as total
                FROM events
                GROUP BY event_type
                """
            ).fetchall()

        metrics = {row["event_type"]: row["total"] for row in rows}
        return jsonify(events=metrics, generated_at=_now())

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5004, debug=True)
