from datetime import datetime
from pathlib import Path
from typing import Dict, List

from flask import Flask, jsonify, request
from flask_cors import CORS

import os
import requests
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

    @app.post("/profiles/<int:user_id>/bio/suggest")
    def suggest_bio(user_id: int):
        """Gera uma bio curta com IA (GROQ) com base nas skills do usuário."""
        api_key = os.getenv("GROQ_API") or os.getenv("GROQ_API_KEY")
        if not api_key:
            return jsonify(error="IA indisponível: configure a variável de ambiente GROQ_API"), 400

        # Buscar skills do usuário
        try:
            skills_res = requests.get(
                f"https://colaboradores-skills.azurewebsites.net/users/{user_id}/skills",
                timeout=8,
            )
            skills = (skills_res.json() or {}).get("skills", []) if skills_res.ok else []
        except requests.exceptions.RequestException:
            skills = []

        skill_lines = [
            f"- {s.get('skill_name','')} ({s.get('proficiency','')})" for s in skills
        ] or ["- Sem skills cadastradas"]
        skills_text = "\n".join(skill_lines)

        prompt = (
            "Gere uma bio curta e objetiva em português (50 a 70 palavras), "
            "focada em impacto e colaboração, com base nas competências abaixo. "
            "Evite listas e emoji. Texto corrido.\n\n"
            f"Competências:\n{skills_text}\n\nFormato: texto puro."
        )

        try:
            groq_res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama3-8b-8192",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Você é um assistente que escreve bios curtas em pt-BR, com clareza e profissionalismo.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.6,
                    "max_tokens": 256,
                },
                timeout=20,
            )
            if not groq_res.ok:
                # Log detalhado no servidor para debug, mas resposta genérica para o cliente
                try:
                    print("[GROQ_ERROR_STATUS]", groq_res.status_code)
                    print("[GROQ_ERROR_BODY]", groq_res.text[:500])
                except Exception:
                    pass
                return jsonify(error="Falha ao gerar bio"), 502
            data = groq_res.json()
            content = (
                ((data or {}).get("choices") or [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            if not content:
                return jsonify(error="Resposta vazia da IA"), 502
            return jsonify(bio_suggestion=content)
        except requests.exceptions.RequestException:
            return jsonify(error="Erro de conexão com a IA"), 502

    return app


# Expose the WSGI application object at module level for gunicorn (app:app)
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
