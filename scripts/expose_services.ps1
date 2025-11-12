# Script para expor serviços localmente com localtunnel
# Execute este script em terminais separados ou use o Windows Terminal com splits

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  EXPONDO MICROSSERVIÇOS COM LOCALTUNNEL" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se localtunnel está instalado
$ltInstalled = Get-Command lt -ErrorAction SilentlyContinue
if (-not $ltInstalled) {
    Write-Host "❌ localtunnel não está instalado." -ForegroundColor Red
    Write-Host "📦 Instalando localtunnel globalmente..." -ForegroundColor Yellow
    npm install -g localtunnel
    Write-Host "✅ localtunnel instalado!" -ForegroundColor Green
    Write-Host ""
}

Write-Host "🚀 Iniciando túneis para os microsserviços..." -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANTE: Mantenha este terminal aberto!" -ForegroundColor Yellow
Write-Host "Os serviços devem estar rodando em Docker (docker compose up)" -ForegroundColor Yellow
Write-Host ""

# Criar jobs em background para cada serviço
Write-Host "📡 Expondo serviços..." -ForegroundColor Cyan
Write-Host ""

# Auth Service
Write-Host "  🔐 auth_service (5001)..." -ForegroundColor White
Start-Process powershell -ArgumentList "-NoExit", "-Command", "lt --port 5001; Read-Host 'Pressione Enter para fechar'"

Start-Sleep -Seconds 2

# Profile Service
Write-Host "  👤 profile_service (5002)..." -ForegroundColor White
Start-Process powershell -ArgumentList "-NoExit", "-Command", "lt --port 5002; Read-Host 'Pressione Enter para fechar'"

Start-Sleep -Seconds 2

# Skills Service
Write-Host "  🎯 skills_service (5003)..." -ForegroundColor White
Start-Process powershell -ArgumentList "-NoExit", "-Command", "lt --port 5003; Read-Host 'Pressione Enter para fechar'"

Start-Sleep -Seconds 2

# Projects Service
Write-Host "  📁 projects_service (5004)..." -ForegroundColor White
Start-Process powershell -ArgumentList "-NoExit", "-Command", "lt --port 5004; Read-Host 'Pressione Enter para fechar'"

Start-Sleep -Seconds 2

# Frontend
Write-Host "  🌐 colaboradores_app (3005)..." -ForegroundColor White
Start-Process powershell -ArgumentList "-NoExit", "-Command", "lt --port 3005; Read-Host 'Pressione Enter para fechar'"

Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
Write-Host "  ✅ TÚNEIS CRIADOS COM SUCESSO!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""
Write-Host "As URLs públicas aparecerão nas janelas abertas." -ForegroundColor Yellow
Write-Host "Copie as URLs e compartilhe com outros grupos." -ForegroundColor Yellow
Write-Host ""
Write-Host "Para parar os túneis: Feche as janelas do PowerShell" -ForegroundColor Cyan
Write-Host ""

Read-Host "Pressione Enter para fechar este script (os túneis continuarão ativos)"
