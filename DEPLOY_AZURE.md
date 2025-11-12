# 🚀 GUIA DE DEPLOY NO AZURE FOR STUDENTS

## 📋 Pré-requisitos
- Conta Azure for Students ativa
- Repositório GitHub (este projeto)
- Azure CLI instalado (opcional, para deploy via terminal)

---

## 🌐 **MÉTODO 1: Deploy via Portal Azure + GitHub Actions (Recomendado)**

### **Passo 1: Criar os Web Apps no Portal Azure**

1. Acesse: https://portal.azure.com
2. Clique em **"Create a resource"** → **"Web App"**

#### **Para cada serviço, criar um Web App:**

**Auth Service:**
- **Name**: `colaboradores-auth` (ou outro nome único)
- **Publish**: Code
- **Runtime stack**: Python 3.12
- **Operating System**: Linux
- **Region**: Brazil South
- **Pricing plan**: Free F1 (Azure for Students)

Repetir para:
- `colaboradores-profile`
- `colaboradores-skills`
- `colaboradores-projects`

---

### **Passo 2: Obter Publish Profiles**

Para cada Web App criado:

1. No Portal Azure, vá até o Web App
2. Clique em **"Download publish profile"** no menu superior
3. Salve o arquivo `.PublishSettings`

Você terá 4 arquivos:
- `colaboradores-auth.PublishSettings`
- `colaboradores-profile.PublishSettings`
- `colaboradores-skills.PublishSettings`
- `colaboradores-projects.PublishSettings`

---

### **Passo 3: Adicionar Secrets no GitHub**

1. No GitHub, vá em: **Settings** → **Secrets and variables** → **Actions**
2. Clique em **"New repository secret"**

Adicionar 4 secrets (um para cada serviço):

**Nome do Secret**: `AZURE_WEBAPP_PUBLISH_PROFILE_AUTH`
**Valor**: Copie TODO o conteúdo do arquivo `colaboradores-auth.PublishSettings`

Repetir para:
- `AZURE_WEBAPP_PUBLISH_PROFILE_PROFILE`
- `AZURE_WEBAPP_PUBLISH_PROFILE_SKILLS`
- `AZURE_WEBAPP_PUBLISH_PROFILE_PROJECTS`

---

### **Passo 4: Ajustar os Workflows**

Abra cada arquivo em `.github/workflows/` e **altere o nome do Web App**:

```yaml
# deploy-auth.yml
app-name: 'SEU-NOME-AQUI'  # Ex: colaboradores-auth-briankfreire
```

Faça isso para os 4 workflows.

---

### **Passo 5: Fazer Deploy**

```bash
# Commit e push
git add .
git commit -m "Add Azure deployment workflows"
git push origin main
```

Os workflows vão rodar automaticamente! Acompanhe em:
- GitHub → **Actions**

---

### **Passo 6: Configurar Startup Command (IMPORTANTE)**

Para cada Web App no Portal Azure:

1. Vá em **Configuration** → **General settings**
2. **Startup Command**: `python app.py`
3. Clique em **Save**

---

### **Passo 7: Testar os Endpoints**

Após o deploy (5-10 minutos), teste:

```bash
# Auth
curl https://colaboradores-auth.azurewebsites.net/health

# Profile
curl https://colaboradores-profile.azurewebsites.net/health

# Skills
curl https://colaboradores-skills.azurewebsites.net/health

# Projects
curl https://colaboradores-projects.azurewebsites.net/health
```

---

## 🌐 **MÉTODO 2: Deploy via Azure CLI (Alternativa Rápida)**

### **Instalar Azure CLI:**
```powershell
# Windows (PowerShell Admin)
winget install Microsoft.AzureCLI
```

### **Login:**
```bash
az login
```

### **Deploy cada serviço:**

```bash
# Auth Service
cd microservices/auth_service
az webapp up --name colaboradores-auth --resource-group rg-colaboradores --runtime "PYTHON:3.12" --sku F1

# Profile Service
cd ../profile_service
az webapp up --name colaboradores-profile --resource-group rg-colaboradores --runtime "PYTHON:3.12" --sku F1

# Skills Service
cd ../skills_service
az webapp up --name colaboradores-skills --resource-group rg-colaboradores --runtime "PYTHON:3.12" --sku F1

# Projects Service
cd ../projects_service
az webapp up --name colaboradores-projects --resource-group rg-colaboradores --runtime "PYTHON:3.12" --sku F1
```

---

## 🎨 **Frontend (Static Web App)**

### **Opção 1: Azure Static Web Apps (Grátis)**

1. No Portal Azure: **Create a resource** → **Static Web App**
2. **Name**: `colaboradores-frontend`
3. **Hosting plan**: Free
4. **Source**: GitHub (conectar repositório)
5. **Build Details**:
   - **App location**: `/microfronts/colaboradores_app`
   - **Output location**: `/` (vazio)

### **Opção 2: Usar Web App com nginx**

Criar mais um Web App:
```bash
az webapp create --name colaboradores-frontend --resource-group rg-colaboradores --runtime "NODE:18-lts"
```

Depois fazer deploy do HTML.

---

## 🔧 **Atualizar URLs no Frontend**

Após deploy, edite `microfronts/colaboradores_app/index.html`:

```javascript
// Trocar de localhost para URLs Azure
const AUTH_URL = 'https://colaboradores-auth.azurewebsites.net';
const PROFILE_URL = 'https://colaboradores-profile.azurewebsites.net';
const SKILLS_URL = 'https://colaboradores-skills.azurewebsites.net';
const PROJECTS_URL = 'https://colaboradores-projects.azurewebsites.net';
```

---

## ⚠️ **Problemas Comuns**

### **1. SQLite não persiste dados**
**Solução**: Usar Azure SQL Database ou PostgreSQL (pago) OU aceitar que dados serão perdidos em restart.

Para projeto de estudante, SQLite é OK (dados temporários).

### **2. App não inicia (502 Bad Gateway)**
**Solução**:
- Verificar **Startup Command**: `python app.py`
- Ver logs: Portal Azure → Web App → **Log stream**

### **3. Timeout após 230s**
**Solução**: Azure Web App Free Tier tem timeout de 230s. Requisições longas falham.

### **4. Cold Start (primeiro acesso lento)**
**Solução**: Normal no Free Tier. Depois de ~20min sem acesso, app "dorme".

---

## 📊 **URLs Finais**

Após deploy, compartilhe com os outros grupos:

```
🔐 Auth:     https://colaboradores-auth.azurewebsites.net
👤 Profile:  https://colaboradores-profile.azurewebsites.net
🎯 Skills:   https://colaboradores-skills.azurewebsites.net
📁 Projects: https://colaboradores-projects.azurewebsites.net
🌐 Frontend: https://colaboradores-frontend.azurewebsites.net
```

---

## 🎯 **Checklist Final**

- [ ] 4 Web Apps criados no Azure
- [ ] Publish profiles baixados
- [ ] Secrets adicionados no GitHub
- [ ] Workflows commitados e rodando
- [ ] Startup command configurado
- [ ] Endpoints `/health` funcionando
- [ ] Frontend com URLs atualizadas
- [ ] URLs compartilhadas com outros grupos

---

## 📞 **Suporte**

Se der erro, veja os logs:
```bash
# Via Azure CLI
az webapp log tail --name colaboradores-auth --resource-group rg-colaboradores
```

Ou no Portal: **Log stream** de cada Web App.

---

**Boa sorte com o deploy! 🚀**
