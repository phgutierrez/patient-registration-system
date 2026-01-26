# ====================================================================
# Script de Criação de Release
# Sistema de Solicitação de Cirurgia - Ortopedia Pediátrica
# ====================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$Version,
    
    [Parameter(Mandatory=$false)]
    [string]$Message = "Release $Version"
)

Write-Host "`n=====================================================================" -ForegroundColor Cyan
Write-Host "  CRIAÇÃO DE RELEASE - v$Version" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan

# Validar formato de versão
if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    Write-Host "`n❌ ERRO: Versão deve estar no formato X.Y.Z (ex: 1.0.0)`n" -ForegroundColor Red
    exit 1
}

$TagName = "v$Version"
$ZipName = "PatientRegistration-v$Version-windows.zip"

Write-Host "`n📋 Informações da Release:" -ForegroundColor Yellow
Write-Host "   Tag: $TagName" -ForegroundColor White
Write-Host "   Arquivo: $ZipName" -ForegroundColor White
Write-Host "   Mensagem: $Message`n" -ForegroundColor White

# Passo 1: Limpar arquivos anteriores
Write-Host "🧹 1/7 - Limpando arquivos anteriores..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path $ZipName) { Remove-Item -Force $ZipName }
Write-Host "   ✅ Limpeza concluída`n" -ForegroundColor Green

# Passo 2: Limpar arquivos .pyc
Write-Host "🧹 2/7 - Removendo arquivos .pyc..." -ForegroundColor Yellow
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "   ✅ Arquivos .pyc removidos`n" -ForegroundColor Green

# Passo 3: Criar build
Write-Host "🔨 3/7 - Criando executável..." -ForegroundColor Yellow
& D:/Users/phgut/OneDrive/Documentos/patient-registration-system/.venv/Scripts/python.exe build_exe.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ ERRO: Falha ao criar executável`n" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ Executável criado`n" -ForegroundColor Green

# Passo 4: Verificar executável
Write-Host "🔍 4/7 - Verificando executável..." -ForegroundColor Yellow
if (-not (Test-Path "dist\PatientRegistration\PatientRegistration.exe")) {
    Write-Host "`n❌ ERRO: Executável não encontrado`n" -ForegroundColor Red
    exit 1
}
$exeSize = (Get-Item "dist\PatientRegistration\PatientRegistration.exe").Length / 1MB
Write-Host "   ✅ Executável encontrado ($([math]::Round($exeSize, 2)) MB)`n" -ForegroundColor Green

# Passo 5: Criar ZIP
Write-Host "📦 5/7 - Comprimindo pasta..." -ForegroundColor Yellow
Compress-Archive -Path "dist\PatientRegistration" -DestinationPath $ZipName -Force
$zipSize = (Get-Item $ZipName).Length / 1MB
Write-Host "   ✅ Arquivo ZIP criado ($([math]::Round($zipSize, 2)) MB)`n" -ForegroundColor Green

# Passo 6: Git commit e push
Write-Host "📝 6/7 - Criando commit..." -ForegroundColor Yellow
git add .
git commit -m "Release $TagName - $Message"
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ⚠️  Nenhuma mudança para commitar ou erro no commit" -ForegroundColor Yellow
}
Write-Host "   ✅ Commit criado`n" -ForegroundColor Green

# Passo 7: Criar e enviar tag
Write-Host "🏷️  7/7 - Criando e enviando tag..." -ForegroundColor Yellow
git tag -a $TagName -m "$Message"
git push origin master
git push origin $TagName
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ ERRO: Falha ao enviar tag para o GitHub`n" -ForegroundColor Red
    Write-Host "Execute manualmente:" -ForegroundColor Yellow
    Write-Host "   git push origin master" -ForegroundColor White
    Write-Host "   git push origin $TagName`n" -ForegroundColor White
    exit 1
}
Write-Host "   ✅ Tag enviada para o GitHub`n" -ForegroundColor Green

# Resumo
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "  ✅ RELEASE PREPARADA COM SUCESSO!" -ForegroundColor Green
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Resumo:" -ForegroundColor Yellow
Write-Host "   Tag criada: $TagName" -ForegroundColor White
Write-Host "   Arquivo ZIP: $ZipName ($([math]::Round($zipSize, 2)) MB)" -ForegroundColor White
Write-Host "   Executável: $([math]::Round($exeSize, 2)) MB" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Próximos passos:" -ForegroundColor Yellow
Write-Host "   1. Acesse: https://github.com/phgutierrez/patient-registration-system/releases/new" -ForegroundColor White
Write-Host "   2. Selecione a tag: $TagName" -ForegroundColor White
Write-Host "   3. Arraste o arquivo: $ZipName" -ForegroundColor White
Write-Host "   4. Preencha a descrição (veja RELEASE_GUIDE.md)" -ForegroundColor White
Write-Host "   5. Clique em 'Publish release'" -ForegroundColor White
Write-Host ""
Write-Host "📝 Dica: Use o template de release notes do RELEASE_GUIDE.md" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

# Abrir automaticamente o navegador (opcional)
$resposta = Read-Host "Deseja abrir o GitHub Releases no navegador agora? (S/N)"
if ($resposta -eq "S" -or $resposta -eq "s") {
    Start-Process "https://github.com/phgutierrez/patient-registration-system/releases/new?tag=$TagName"
}
