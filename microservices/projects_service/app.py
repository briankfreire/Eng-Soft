from datetime import datetime
from pathlib import Path
from typing import Dict, List

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import sqlite3


DATABASE_PATH = Path(__file__).with_name("projects.db")
PROJETOS_API_URL = "https://bdprojetos.azurewebsites.net"


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Cria tabela para vincular colaboradores aos projetos."""
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_collaborators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                skill_name TEXT,
                skill_level TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(project_id, user_id)
            )
            """
        )
        conn.commit()


def create_app() -> Flask:
    """Factory que configura e retorna o app Flask."""
    init_db()
    app = Flask(__name__)
    CORS(app)

    @app.get("/health")
    def health():
        return jsonify(status="ok", service="projects_service", timestamp=_now())

    @app.post("/projects/<int:project_id>/collaborators/<int:user_id>")
    def link_collaborator(project_id: int, user_id: int):
        """Vincula colaborador ao projeto e notifica API externa."""
        try:
            # 1. Buscar dados do colaborador nos outros serviços
            profile_url = f"http://profile_service:5002/profiles/{user_id}"
            skills_url = f"http://skills_service:5003/users/{user_id}/skills"
            
            try:
                profile_res = requests.get(profile_url, timeout=5)
                skills_res = requests.get(skills_url, timeout=5)
            except requests.exceptions.RequestException as e:
                return jsonify(error=f"Erro ao buscar dados do colaborador: {str(e)}"), 500

            if profile_res.status_code != 200:
                return jsonify(error="Perfil não encontrado"), 404
            if skills_res.status_code != 200:
                return jsonify(error="Skills não encontradas"), 404

            profile_data = profile_res.json().get("profile", {})
            skills_data = skills_res.json().get("skills", [])

            # 2. Pegar primeira skill (ou usar padrão)
            main_skill = skills_data[0] if skills_data else {}
            skill_name = main_skill.get("skill_name", "Geral")
            skill_level = main_skill.get("proficiency", "basic")

            # 3. Buscar email do auth_service
            auth_url = f"http://auth_service:5001/users/{user_id}"
            try:
                auth_res = requests.get(auth_url, timeout=5)
                if auth_res.status_code != 200:
                    return jsonify(error="Usuário não encontrado no auth"), 404
                user_data = auth_res.json().get("user", {})
                email = user_data.get("email", "")
            except requests.exceptions.RequestException:
                return jsonify(error="Erro ao buscar email do usuário"), 500

            # 4. Verificar se já está vinculado
            with get_conn() as conn:
                existing = conn.execute(
                    "SELECT id FROM project_collaborators WHERE project_id = ? AND user_id = ?",
                    (project_id, user_id)
                ).fetchone()
                if existing:
                    return jsonify(error="Colaborador já vinculado a este projeto"), 409

            # 5. Notificar API externa de Projetos
            payload = {
                "collaborator_email": email,
                "contributed_skill_name": skill_name,
                "contributed_skill_level": skill_level
            }
            
            try:
                external_res = requests.post(
                    f"{PROJETOS_API_URL}/projects/{project_id}/members",
                    json=payload,
                    timeout=10
                )
                if external_res.status_code not in (200, 201):
                    return jsonify(
                        error=f"Falha ao notificar API de Projetos: {external_res.text}"
                    ), 500
            except requests.exceptions.RequestException as e:
                return jsonify(error=f"Erro ao conectar à API de Projetos: {str(e)}"), 500

            # 6. Salvar vínculo localmente
            with get_conn() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO project_collaborators (project_id, user_id, skill_name, skill_level, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (project_id, user_id, skill_name, skill_level, _now())
                )
                conn.commit()
                link_id = cursor.lastrowid

            return jsonify(
                message="Colaborador vinculado com sucesso",
                link_id=link_id,
                project_id=project_id,
                user_id=user_id,
                skill_name=skill_name,
                skill_level=skill_level
            ), 201

        except Exception as e:
            return jsonify(error=f"Erro interno: {str(e)}"), 500

    @app.get("/projects/<int:project_id>/collaborators")
    def list_project_collaborators(project_id: int):
        """Lista colaboradores de um projeto."""
        with get_conn() as conn:
            rows = conn.execute(
                """
                SELECT id, user_id, skill_name, skill_level, created_at
                FROM project_collaborators
                WHERE project_id = ?
                ORDER BY created_at DESC
                """,
                (project_id,)
            ).fetchall()

        collaborators = [
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "skill_name": row["skill_name"],
                "skill_level": row["skill_level"],
                "created_at": row["created_at"]
            }
            for row in rows
        ]

        return jsonify(project_id=project_id, collaborators=collaborators)

    @app.get("/collaborators/<int:user_id>/projects")
    def list_user_projects(user_id: int):
        """Lista projetos de um colaborador."""
        with get_conn() as conn:
            rows = conn.execute(
                """
                SELECT id, project_id, skill_name, skill_level, created_at
                FROM project_collaborators
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,)
            ).fetchall()

        projects = [
            {
                "id": row["id"],
                "project_id": row["project_id"],
                "skill_name": row["skill_name"],
                "skill_level": row["skill_level"],
                "created_at": row["created_at"]
            }
            for row in rows
        ]

        return jsonify(user_id=user_id, projects=projects)

    @app.delete("/projects/<int:project_id>/collaborators/<int:user_id>")
    def unlink_collaborator(project_id: int, user_id: int):
        """Remove vínculo entre colaborador e projeto."""
        with get_conn() as conn:
            deleted = conn.execute(
                "DELETE FROM project_collaborators WHERE project_id = ? AND user_id = ?",
                (project_id, user_id)
            )
            if deleted.rowcount == 0:
                return jsonify(error="Vínculo não encontrado"), 404
            conn.commit()

        return jsonify(message="Colaborador removido do projeto"), 200

    @app.get("/metrics")
    def metrics():
        """Métricas simples."""
        with get_conn() as conn:
            total_links = conn.execute(
                "SELECT COUNT(*) as count FROM project_collaborators"
            ).fetchone()["count"]
            
            unique_projects = conn.execute(
                "SELECT COUNT(DISTINCT project_id) as count FROM project_collaborators"
            ).fetchone()["count"]
            
            unique_collaborators = conn.execute(
                "SELECT COUNT(DISTINCT user_id) as count FROM project_collaborators"
            ).fetchone()["count"]

        return jsonify(
            total_links=total_links,
            unique_projects=unique_projects,
            unique_collaborators=unique_collaborators,
            generated_at=_now()
        )

    @app.get("/proxy/projects")
    def proxy_list_projects():
        """Proxy para listar projetos da API externa (contorna CORS)."""
        search_term = request.args.get("q", "")
        
        try:
            url = f"{PROJETOS_API_URL}/projects"
            if search_term:
                url += f"?q={search_term}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify(error="Erro ao buscar projetos", details=response.text), response.status_code
        except requests.exceptions.RequestException as e:
            return jsonify(error=f"Erro de conexão: {str(e)}"), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5004, debug=True)
