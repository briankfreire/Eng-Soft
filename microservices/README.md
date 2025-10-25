# MVP de Microsserviços – Plataforma de Colaboração

Este diretório contém o MVP dos microsserviços solicitados para o projeto descrito em
`docs/projeto.md`, com foco nas histórias de usuário da primeira Sprint (US001-US007). O
objetivo é entregar valor rapidamente e permitir a medição de uso logo nas primeiras
interações.

## Visão Geral dos Serviços

- **Auth Service (`auth_service`)** – Garante cadastro, autenticação básica e métricas de uso.
- **Profile Service (`profile_service`)** – Mantém as informações públicas do perfil do colaborador.
- **Skills Service (`skills_service`)** – Controla o catálogo de competências e o vínculo com colaboradores.
- **Analytics Service (`analytics_service`)** – Armazena eventos simples para acompanhamento de adoção.

Cada serviço é isolado, usa SQLite local para facilitar demonstrações offline e expõe um
endpoint `/health` e um `/metrics` para visibilidade operacional.

## Como Executar

```bash
cd microservices/<nome_do_servico>
python3 app.py  # Flask nativo, porta dedicada por serviço
```

Portas padrão:

| Serviço              | Porta |
| -------------------- | ----- |
| Auth Service         | 5001  |
| Profile Service      | 5002  |
| Skills Service       | 5003  |
| Analytics Service    | 5004  |

Para instalar dependências (quando necessário):

```bash
pip install -r requirements.txt
```

## Dados de Demonstração

Execute o script `scripts/seed_demo_data.py` na raiz do projeto (após instalar as dependências do Auth Service, que incluem o `Werkzeug`) para popular os bancos SQLite com dados prontos para apresentação:

```bash
python3 scripts/seed_demo_data.py
```

O seed cria dois colaboradores principais:

- `sofia.dev@example.com` – senha `colab123`
- `mateus.ux@example.com` – senha `designer123`

Com isso, os microfronts já exibem perfis preenchidos, habilidades associadas, eventos de analytics e métricas com valores significativos logo na primeira demonstração.

## Endpoints Principais

### Auth Service (`auth_service/app.py`)

- `POST /register` – Cria usuário com `email` e `password` (>= 6 caracteres).
- `POST /login` – Valida credenciais e registra evento de sucesso/falha.
- `GET /users/<user_id>` – Retorna dados básicos do usuário.
- `GET /metrics` – Quantidade de usuários e resultado dos logins.

### Profile Service (`profile_service/app.py`)

- `PUT /profiles/<user_id>` – Cria ou atualiza perfil (nome obrigatório, estado de disponibilidade validado).
- `GET /profiles/<user_id>` – Exibe perfil + links + percentual de completude.
- `POST /profiles/<user_id>/links` – Adiciona link externo (ex.: LinkedIn).
- `DELETE /profiles/<user_id>/links/<link_id>` – Remove link cadastrado.
- `GET /profiles/<user_id>/completeness` – Retorna pontuação simplificada.
- `GET /metrics` – Número total de perfis, disponibilidade e média de links.

### Skills Service (`skills_service/app.py`)

- `GET /skills` – Lista de competências aprovadas e pendentes.
- `POST /skills` – Administra cadastro/sugestão de habilidades (status `approved` ou `pending`).
- `POST /users/<user_id>/skills` – Vincula competência ao colaborador (aceita `skill_id` ou `skill_name`).
- `GET /users/<user_id>/skills` – Lista competências com proficiência (`basic`, `intermediate`, `advanced`).
- `DELETE /users/<user_id>/skills/<id>` – Remove vínculo com competência.
- `GET /metrics` – Quantidade total de skills, pendências e distribuição de proficiências.

### Analytics Service (`analytics_service/app.py`)

- `POST /events` – Registra eventos customizados (`event_type`, `user_id`, `payload` livre).
- `GET /events/recent` – Últimos eventos (limite 1-100, padrão 10).
- `GET /metrics` – Contagem por tipo de evento, para acompanhar adoção das funcionalidades.

## Fluxo Recomendado para Demonstração

1. **Cadastro** (`auth_service`): criar usuário e efetuar login.
2. **Perfil** (`profile_service`): preencher dados e adicionar links; observar `/metrics` para acompanhar qualidade do perfil.
3. **Competências** (`skills_service`): consumir lista, adicionar habilidades com proficiência e testar sugestão automática.
4. **Medição** (`analytics_service`): registrar eventos como `project.viewed` ou `profile.completed` para mostrar alinhamento com a diretriz de medir sucesso.

## Próximos Passos Sugeridos

- Adicionar autenticação baseada em tokens entre os serviços.
- Criar gateway/API Gateway simples para orquestrar chamadas.
- Conectar o `analytics_service` com dashboards ou ferramentas de visualização.
