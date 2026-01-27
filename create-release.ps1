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
$Python64bitPath = "D:/Users/phgut/OneDrive/Documentos/patient-registration-system/.venv/Scripts/python.exe"
$Python32bitPath = "D:/Users/phgut/OneDrive/Documentos/patient-registration-system/.venv32/Scripts/python.exe"

Write-Host "`n📋 Informações da Release:" -ForegroundColor Yellow
Write-Host "   Tag: $TagName" -ForegroundColor White
Write-Host "   Arquivo: $ZipName" -ForegroundColor White
Write-Host "   Mensagem: $Message`n" -ForegroundColor White
Write-Host "   Será criado: Sistema64bits + Sistema32bits`n" -ForegroundColor Cyan

# Passo 1: Limpar arquivos anteriores
Write-Host "🧹 1/9 - Limpando arquivos anteriores..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path $ZipName) { Remove-Item -Force $ZipName }
Write-Host "   ✅ Limpeza concluída`n" -ForegroundColor Green

# Passo 2: Limpar arquivos .pyc
Write-Host "🧹 2/9 - Removendo arquivos .pyc..." -ForegroundColor Yellow
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "   ✅ Arquivos .pyc removidos`n" -ForegroundColor Green

# Passo 3: Criar build 64bits
Write-Host "🔨 3/9 - Criando executável 64bits..." -ForegroundColor Yellow
& $Python64bitPath build_exe.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ ERRO: Falha ao criar executável 64bits`n" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ Executável 64bits criado`n" -ForegroundColor Green

# Passo 4: Verificar executável 64bits
Write-Host "🔍 4/9 - Verificando executável 64bits..." -ForegroundColor Yellow
if (-not (Test-Path "dist\Sistema64bits\PatientRegistration\PatientRegistration.exe")) {
    Write-Host "`n❌ ERRO: Executável 64bits não encontrado`n" -ForegroundColor Red
    exit 1
}
$exe64Size = (Get-Item "dist\Sistema64bits\PatientRegistration\PatientRegistration.exe").Length / 1MB
Write-Host "   ✅ Executável 64bits encontrado ($([math]::Round($exe64Size, 2)) MB)`n" -ForegroundColor Green

# Passo 5: Criar build 32bits
Write-Host "🔨 5/9 - Criando executável 32bits..." -ForegroundColor Yellow
# Tentar usar Python 64bits para gerar 32bits
& $Python64bitPath build_exe_32bits.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n⚠️  AVISO: Falha ao criar executável 32bits com Python 64bits" -ForegroundColor Yellow
    Write-Host "   Verificando se já existe build 32bits anterior..." -ForegroundColor Yellow
    if (Test-Path "dist\Sistema32bits\PatientRegistration\PatientRegistration.exe") {
        Write-Host "   ✅ Usando build 32bits anterior`n" -ForegroundColor Green
        $Skip32bit = $false
    } else {
        Write-Host "   Pulando build 32bits. Nenhum build anterior encontrado." -ForegroundColor Yellow
        $Skip32bit = $true
    }
} else {
    Write-Host "   ✅ Executável 32bits criado`n" -ForegroundColor Green
    $Skip32bit = $false
}

# Passo 6: Verificar executável 32bits
if (-not $Skip32bit) {
    Write-Host "🔍 6/9 - Verificando executável 32bits..." -ForegroundColor Yellow
    if (-not (Test-Path "dist\Sistema32bits\PatientRegistration\PatientRegistration.exe")) {
        Write-Host "`n❌ ERRO: Executável 32bits não encontrado`n" -ForegroundColor Red
        exit 1
    }
    $exe32Size = (Get-Item "dist\Sistema32bits\PatientRegistration\PatientRegistration.exe").Length / 1MB
    Write-Host "   ✅ Executável 32bits encontrado ($([math]::Round($exe32Size, 2)) MB)`n" -ForegroundColor Green
    $CurrentStep = 7
} else {
    $CurrentStep = 6
}

# Passo 7/6: Criar ZIP com ambos os executáveis
Write-Host "📦 $CurrentStep/9 - Comprimindo arquivos..." -ForegroundColor Yellow
# Criar estrutura temporária para o ZIP
$tempZipPath = "temp_release"
if (Test-Path $tempZipPath) { Remove-Item -Recurse -Force $tempZipPath }
New-Item -ItemType Directory -Path $tempZipPath | Out-Null
New-Item -ItemType Directory -Path "$tempZipPath\Sistema64bits" | Out-Null

# Copiar 64bits
Copy-Item -Path "dist\Sistema64bits\PatientRegistration" -Destination "$tempZipPath\Sistema64bits\" -Recurse

# Copiar 32bits se existir
if (-not $Skip32bit) {
    New-Item -ItemType Directory -Path "$tempZipPath\Sistema32bits" | Out-Null
    Copy-Item -Path "dist\Sistema32bits\PatientRegistration" -Destination "$tempZipPath\Sistema32bits\" -Recurse
}

# Criar ZIP
Compress-Archive -Path "$tempZipPath\*" -DestinationPath $ZipName -Force

# Limpar temporário
Remove-Item -Recurse -Force $tempZipPath

$zipSize = (Get-Item $ZipName).Length / 1MB
if (-not $Skip32bit) {
    Write-Host "   ✅ Arquivo ZIP criado com 64bits e 32bits ($([math]::Round($zipSize, 2)) MB)`n" -ForegroundColor Green
} else {
    Write-Host "   ✅ Arquivo ZIP criado com 64bits ($([math]::Round($zipSize, 2)) MB)`n" -ForegroundColor Green
}

# Passo 8: Git commit e push
Write-Host "$([math]::Round($CurrentStep)+1)/9 - Criando commit..." -ForegroundColor Yellow
git add .
git commit -m "Release $TagName - $Message"
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ⚠️  Nenhuma mudança para commitar ou erro no commit" -ForegroundColor Yellow
}
Write-Host "   ✅ Commit criado`n" -ForegroundColor Green

# Passo 9: Criar e enviar tag
Write-Host "$([math]::Round($CurrentStep)+2)/9 - Criando e enviando tag..." -ForegroundColor Yellow
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
if (-not $Skip32bit) {
    Write-Host "   Executável 64bits: $([math]::Round($exe64Size, 2)) MB" -ForegroundColor White
    Write-Host "   Executável 32bits: $([math]::Round($exe32Size, 2)) MB" -ForegroundColor White
} else {
    Write-Host "   Executável 64bits: $([math]::Round($exe64Size, 2)) MB" -ForegroundColor White
    Write-Host "   Executável 32bits: ⚠️  Não foi criado (configure Python 32bits)" -ForegroundColor Yellow
}
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
