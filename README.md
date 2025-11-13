# 🚀 TeamBuilder (Grupo Colaboradores)

Microsserviços para autenticação, perfis, competências e vínculo com projetos.

## 📋 Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    MICROSSERVIÇOS                           │
├─────────────────────────────────────────────────────────────┤
│  1. auth_service (5001)      → Autenticação                │
│  2. profile_service (5002)   → Perfis dos colaboradores    │
│  3. skills_service (5003)    → Competências e proficiência │
│  4. projects_service (5004)  → Vínculo colaborador↔projeto │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND                                 │
├─────────────────────────────────────────────────────────────┤
│  colaboradores_app (3005)    → Interface unificada         │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Executar localmente

Pré-requisitos: Docker e Docker Compose.

```powershell
cd infra/docker
docker compose up --build
```

- Frontend: http://localhost:3005
- Auth:     http://localhost:5001
- Profile:  http://localhost:5002
- Skills:   http://localhost:5003
- Projects: http://localhost:5004

## 📡 Endpoints principais

Auth (5001)
```
POST /register
POST /login
GET  /users/{id}
GET  /metrics
```

Profile (5002)
```
PUT    /profiles/{user_id}
GET    /profiles/{user_id}
POST   /profiles/{user_id}/links
DELETE /profiles/{user_id}/links/{id}
GET    /profiles/{user_id}/completeness
GET    /metrics
```

Skills (5003)
```
GET    /skills
POST   /skills
POST   /users/{user_id}/skills
GET    /users/{user_id}/skills
DELETE /users/{user_id}/skills/{id}
GET    /metrics
```

Projects (5004)
```
POST   /projects/{project_id}/collaborators/{user_id}
GET    /projects/{project_id}/collaborators
GET    /collaborators/{user_id}/projects
DELETE /projects/{project_id}/collaborators/{user_id}
GET    /metrics
```

Notas do Projects:
- Integra com `https://bdprojetos.azurewebsites.net`.
- Join idempotente: se a API externa retornar 409 “already linked”, salvamos localmente e retornamos sucesso.
- Proxy: `GET /proxy/projects` lista projetos externos (usado pelo frontend e cache de títulos).

## 🌐 URLs de produção (Azure)

- Auth:     https://colaboradores-auth.azurewebsites.net
- Profile:  https://colaboradores-profile.azurewebsites.net
- Skills:   https://colaboradores-skills.azurewebsites.net
- Projects: https://colaboradores-projects.azurewebsites.net
- Frontend (Pages): GitHub Pages via workflow

Observações:
- Cada serviço expõe `app:app` (Gunicorn) para Azure.
- Workflows empacotam dependências no artefato (pip -t .) para evitar falhas do Oryx.

## 📦 Estrutura

```
microservices/
  auth_service/|profile_service/|skills_service/|projects_service/
    app.py, Dockerfile, requirements.txt, *.db (gerado)
microfronts/
  colaboradores_app/index.html
infra/docker/docker-compose.yml
.github/workflows/ci.yml
requirements-dev.txt, pyproject.toml, .pre-commit-config.yaml
```

## 🧪 Testes e qualidade

- Testes (pytest) para `projects_service` em `microservices/projects_service/tests`.
- Lint/format com Ruff e Black (config em `pyproject.toml`).
- CI (`.github/workflows/ci.yml`): instala deps, roda Ruff, Black (check) e pytest.

Instalar ferramentas locais (opcional):
```powershell
pip install -r requirements-dev.txt
ruff check .
black .
pytest -q
```

## 🔗 Integração externa

`projects_service` usa `bdprojetos.azurewebsites.net`:
- POST `/projects/{id}/members` com `{collaborator_email, contributed_skill_name, contributed_skill_level}`.
- GET `/projects` (via proxy) e GET `/projects/{id}` para título.

## 🧰 Troubleshooting rápido

- Ver logs: `docker compose logs <service>`
- Portas ocupadas: `docker compose down`; use `netstat -ano | findstr :500x`
- API externa 409: comportamento esperado (idempotente); ver “Meus Projetos”.

## 👥 Equipe

Grupo Colaboradores — Engenharia de Software (Mackenzie)

## 📄 Licença

Uso acadêmico
