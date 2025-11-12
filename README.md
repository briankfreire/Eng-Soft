# 🚀 GRUPO COLABORADORES - TeamBuilder

Sistema de microsserviços para gerenciar perfis de colaboradores, suas competências e vínculos com projetos.

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

---

## 🔧 Como Rodar Localmente

### **1. Pré-requisitos**
- Docker + Docker Compose instalados
- Git

### **2. Subir os serviços**
```powershell
# No diretório raiz do projeto
cd infra/docker
docker compose up --build
```

### **3. Acessar**
- Frontend: http://localhost:3005
- Auth API: http://localhost:5001
- Profile API: http://localhost:5002
- Skills API: http://localhost:5003
- Projects API: http://localhost:5004

---

## 📡 Endpoints Principais

### **AUTH SERVICE (5001)**
```
POST   /register          → Cadastrar colaborador
POST   /login             → Autenticar
GET    /users/{id}        → Buscar usuário
GET    /metrics           → Métricas de autenticação
```

### **PROFILE SERVICE (5002)**
```
PUT    /profiles/{user_id}              → Criar/atualizar perfil
GET    /profiles/{user_id}              → Buscar perfil
POST   /profiles/{user_id}/links        → Adicionar link externo
DELETE /profiles/{user_id}/links/{id}   → Remover link
GET    /profiles/{user_id}/completeness → Completude do perfil
GET    /metrics                         → Métricas de perfis
```

### **SKILLS SERVICE (5003)**
```
GET    /skills                      → Listar catálogo de skills
POST   /skills                      → Criar nova skill
POST   /users/{user_id}/skills      → Adicionar skill ao colaborador
GET    /users/{user_id}/skills      → Listar skills do colaborador
DELETE /users/{user_id}/skills/{id} → Remover skill
GET    /metrics                     → Métricas de skills
```

### **PROJECTS SERVICE (5004)** 🆕
```
POST   /projects/{project_id}/collaborators/{user_id}
  → Vincula colaborador ao projeto
  → Integra com https://bdprojetos.azurewebsites.net

GET    /projects/{project_id}/collaborators
  → Lista colaboradores do projeto

GET    /collaborators/{user_id}/projects
  → Lista projetos do colaborador

DELETE /projects/{project_id}/collaborators/{user_id}
  → Remove vínculo

GET    /metrics
  → Métricas de vínculos
```

---

## 🌐 Expor Localmente (para testes com outros grupos)

### **Opção 1: Localtunnel (rápido)**
```powershell
# Instalar localtunnel globalmente
npm install -g localtunnel

# Expor cada serviço (em terminais separados)
lt --port 5001 --subdomain colaboradores-auth
lt --port 5002 --subdomain colaboradores-profile
lt --port 5003 --subdomain colaboradores-skills
lt --port 5004 --subdomain colaboradores-projects
lt --port 3005 --subdomain colaboradores-app
```

**URLs geradas:**
```
https://colaboradores-auth.loca.lt
https://colaboradores-profile.loca.lt
https://colaboradores-skills.loca.lt
https://colaboradores-projects.loca.lt
https://colaboradores-app.loca.lt
```

### **Opção 2: ngrok (alternativa)**
```powershell
# Expor um serviço por vez
ngrok http 5001
ngrok http 5002
ngrok http 5003
ngrok http 5004
ngrok http 3005
```

---

## 🔗 Integração com Outros Grupos

### **Com Grupo Projetos (bdprojetos.azurewebsites.net)**

O `projects_service` automaticamente notifica a API externa ao vincular um colaborador:

```javascript
// Quando colaborador se vincula a um projeto:
POST http://localhost:5004/projects/123/collaborators/456

// Internamente, o projects_service faz:
1. Busca perfil em profile_service (5002)
2. Busca skills em skills_service (5003)
3. Busca email em auth_service (5001)
4. Envia para bdprojetos.azurewebsites.net:
   POST /projects/123/members
   {
     "collaborator_email": "email@example.com",
     "contributed_skill_name": "Python",
     "contributed_skill_level": "advanced"
   }
```

### **Com Grupo Login (loginidealizador.azurewebsites.net)**

O `auth_service` pode receber JWT do grupo Login (futuro):
- Header `X-User-Email` para identificar usuário
- Header `Authorization: Bearer <token>` para validação

### **Com Grupo IA (iaidealizador.azurewebsites.net)**

O `skills_service` pode receber sugestões da IA (futuro):
- Endpoint para enriquecer perfil com skills sugeridas
- Auto-completar competências baseado em descrição

---

## 📦 Estrutura do Projeto

```
microservices/
  auth_service/
    app.py
    Dockerfile
    requirements.txt
    auth.db (gerado automaticamente)
  
  profile_service/
    app.py
    Dockerfile
    requirements.txt
    profiles.db (gerado automaticamente)
  
  skills_service/
    app.py
    Dockerfile
    requirements.txt
    skills.db (gerado automaticamente)
  
  projects_service/
    app.py
    Dockerfile
    requirements.txt
    projects.db (gerado automaticamente)

microfronts/
  colaboradores_app/
    index.html (frontend unificado)

infra/
  docker/
    docker-compose.yml
```

---

## 🚀 Deploy no Azure (próximo passo)

### **Criar Web Apps:**
```bash
# Azure CLI
az group create --name rg-colaboradores --location brazilsouth

# Criar 4 Web Apps (uma para cada serviço)
az webapp up --name colaboradores-auth --resource-group rg-colaboradores --runtime "PYTHON:3.12"
az webapp up --name colaboradores-profile --resource-group rg-colaboradores --runtime "PYTHON:3.12"
az webapp up --name colaboradores-skills --resource-group rg-colaboradores --runtime "PYTHON:3.12"
az webapp up --name colaboradores-projects --resource-group rg-colaboradores --runtime "PYTHON:3.12"
```

### **GitHub Actions:**
- Push na `main` → deploy automático
- Workflows já estão em `.github/workflows/ci.yml`

---

## 🧪 Testar Endpoints

### **1. Cadastrar e fazer login:**
```bash
# Cadastrar
curl -X POST http://localhost:5001/register \
  -H "Content-Type: application/json" \
  -d '{"email":"teste@example.com","password":"senha123"}'

# Login
curl -X POST http://localhost:5001/login \
  -H "Content-Type: application/json" \
  -d '{"email":"teste@example.com","password":"senha123"}'
# Resposta: {"message":"login ok","user":{"id":1,"email":"teste@example.com"}}
```

### **2. Criar perfil:**
```bash
curl -X PUT http://localhost:5002/profiles/1 \
  -H "Content-Type: application/json" \
  -d '{"full_name":"João Silva","bio":"Desenvolvedor Full Stack","availability":"actively-looking"}'
```

### **3. Adicionar skill:**
```bash
curl -X POST http://localhost:5003/users/1/skills \
  -H "Content-Type: application/json" \
  -d '{"skill_name":"Python","proficiency":"advanced"}'
```

### **4. Vincular a projeto:**
```bash
curl -X POST http://localhost:5004/projects/123/collaborators/1
# Isso notifica automaticamente bdprojetos.azurewebsites.net
```

---

## 📝 Notas Importantes

- **SQLite**: Cada serviço tem seu próprio banco `.db` (gerado automaticamente)
- **CORS**: Todos os serviços aceitam requisições de qualquer origem (ajustar para produção)
- **Erros**: Logs aparecem no console do Docker Compose
- **Dados**: SQLite persiste em volumes Docker (data fica salva entre restarts)

---

## 🆘 Troubleshooting

### **Erro "address already in use"**
```powershell
# Parar containers
docker compose down

# Verificar portas ocupadas
netstat -ano | findstr :5001
netstat -ano | findstr :5002
# etc...

# Matar processo (se necessário)
taskkill /PID <PID> /F
```

### **Serviço não responde**
```powershell
# Ver logs
docker compose logs auth_service
docker compose logs profile_service
docker compose logs skills_service
docker compose logs projects_service
```

### **Erro de integração com bdprojetos**
- Verificar se a URL `https://bdprojetos.azurewebsites.net` está acessível
- Ver logs do `projects_service` para detalhes do erro
- Testar manualmente: `curl https://bdprojetos.azurewebsites.net/projects`

---

## 👥 Equipe

**Grupo Colaboradores** - Engenharia de Software - Mackenzie 2025

---

## 📄 Licença

Projeto acadêmico - Mackenzie
