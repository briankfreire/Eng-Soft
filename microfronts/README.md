# Microfronts para Demonstração do MVP

Cada microfrontend é uma página HTML+JS estática construída para interagir diretamente
com um dos microsserviços presentes em `../microservices`. O objetivo é oferecer uma
experiência rápida para validar as histórias da Sprint 1 e mostrar como o time já mede
sucesso logo no MVP.

## Como executar

1. Certifique-se de estar com os microsserviços desejados ativos (ex.: `python3 app.py` em
   cada pasta de `../microservices`).
2. (Opcional recomendado) Popule dados mockados com `python3 ../scripts/seed_demo_data.py`
   para já iniciar a demo com usuários, perfis, skills e eventos registrados.
3. Servir as páginas estáticas com um servidor simples (ex.: `python3 -m http.server 8000`
   dentro do diretório `microfronts`) ou abrir os arquivos diretamente no navegador.
4. Acesse a página correspondente:

| Microfront          | Caminho                          | Porta backend | Objetivo principal                               |
| ------------------- | -------------------------------- | ------------- | ------------------------------------------------- |
| Auth Front          | `auth_app/index.html`            | 5001          | Cadastro/login de colaboradores e métricas iniciais |
| Profile Front       | `profile_app/index.html`         | 5002          | Atualização do perfil, links e completude         |
| Skills Front        | `skills_app/index.html`          | 5003          | Gestão de catálogo e proficiências                |
| Analytics Front     | `analytics_app/index.html`       | 5004          | Registro de eventos e acompanhamento de métricas  |

> Dica: execute `python3 -m http.server 8000` dentro de `microfronts` e acesse
> `http://localhost:8000/auth_app/index.html` (substituindo pelo microfront desejado).

## Fluxo sugerido para demonstração

1. **Autenticação**: criar usuário no Auth Front, efetuar login e inspecionar métricas para exibir
   contagem de sucesso/falha de logins.
2. **Perfil**: com o user ID obtido, atualizar o perfil no Profile Front, adicionar links e evidenciar a
   métrica de completude.
3. **Competências**: no Skills Front, visualizar catálogo inicial, associar habilidades ao usuário e
   mostrar distribuição de proficiências.
4. **Medição**: registrar eventos relevantes (ex.: `profile.completed`) no Analytics Front e exibir os
   eventos recentes e contagem por tipo.

## Próximos passos possíveis

- Criar um layout comum compartilhado entre os microfronts (design system leve).
- Realizar deploy dos microfronts via GitHub Pages ou serviço similar para facilitar testes com
  stakeholders.
- Integrar os microfronts a um gateway/api gateway para simplificar as URLs expostas.
