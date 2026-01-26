# ====================================================================
# Script de Criação de Release Multi-Arquitetura
# Sistema de Solicitação de Cirurgia - Ortopedia Pediátrica
# Versão: 1.0.1 - Suporte 32 e 64 bits
# ====================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$Version,
    
    [Parameter(Mandatory=$false)]
    [string]$Message = "Release $Version"
)

Write-Host "`n=====================================================================" -ForegroundColor Cyan
Write-Host "  CRIAÇÃO DE RELEASE MULTI-ARQUITETURA - v$Version" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan

# Validar formato de versão
if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    Write-Host "`n❌ ERRO: Versão deve estar no formato X.Y.Z (ex: 1.0.1)`n" -ForegroundColor Red
    exit 1
}

$TagName = "v$Version"
$ZipName = "PatientRegistration-v$Version-windows.zip"
$VenvPath = "D:/Users/phgut/OneDrive/Documentos/patient-registration-system/.venv"
$Venv32Path = "D:/Users/phgut/OneDrive/Documentos/patient-registration-system/.venv32"

Write-Host "`n📋 Informações da Release:" -ForegroundColor Yellow
Write-Host "   Tag: $TagName" -ForegroundColor White
Write-Host "   Arquivo: $ZipName" -ForegroundColor White
Write-Host "   Mensagem: $Message`n" -ForegroundColor White

# Passo 1: Limpar arquivos anteriores
Write-Host "🧹 1/8 - Limpando arquivos anteriores..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path $ZipName) { Remove-Item -Force $ZipName }
Write-Host "   ✅ Limpeza concluída`n" -ForegroundColor Green

# Passo 2: Limpar arquivos .pyc
Write-Host "🧹 2/8 - Removendo arquivos .pyc..." -ForegroundColor Yellow
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "   ✅ Arquivos .pyc removidos`n" -ForegroundColor Green

# Passo 3: Criar executável 64 bits
Write-Host "🔨 3/8 - Criando executável 64 bits..." -ForegroundColor Yellow
& "$VenvPath/Scripts/python.exe" build_exe.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ ERRO: Falha ao criar executável 64 bits`n" -ForegroundColor Red
    exit 1
}

# Renomear pasta dist para preservar build 64 bits
if (Test-Path "dist\PatientRegistration") {
    Rename-Item "dist\PatientRegistration" "dist\PatientRegistration-64bit"
    Write-Host "   ✅ Executável 64 bits criado`n" -ForegroundColor Green
} else {
    Write-Host "`n❌ ERRO: Pasta dist\PatientRegistration não encontrada`n" -ForegroundColor Red
    exit 1
}

# Passo 4: Verificar se existe ambiente Python 32 bits
Write-Host "🔨 4/8 - Verificando ambiente Python 32 bits..." -ForegroundColor Yellow
if (-not (Test-Path $Venv32Path)) {
    Write-Host "   ⚠️  Ambiente Python 32 bits não encontrado" -ForegroundColor Yellow
    Write-Host "   Criando ambiente 32 bits..." -ForegroundColor Yellow
    
    # Tentar criar ambiente 32 bits
    try {
        & py -3.11-32 -m venv .venv32
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Ambiente 32 bits criado" -ForegroundColor Green
            Write-Host "   Instalando dependências..." -ForegroundColor Yellow
            & "$Venv32Path\Scripts\python.exe" -m pip install --upgrade pip
            & "$Venv32Path\Scripts\python.exe" -m pip install -r requirements.txt
            Write-Host "   ✅ Dependências instaladas`n" -ForegroundColor Green
        } else {
            Write-Host "`n   ⚠️  Python 32 bits não instalado no sistema" -ForegroundColor Yellow
            Write-Host "   Continuando apenas com versão 64 bits...`n" -ForegroundColor Yellow
            $Skip32Bit = $true
        }
    } catch {
        Write-Host "`n   ⚠️  Não foi possível criar ambiente 32 bits" -ForegroundColor Yellow
        Write-Host "   Continuando apenas com versão 64 bits...`n" -ForegroundColor Yellow
        $Skip32Bit = $true
    }
} else {
    Write-Host "   ✅ Ambiente 32 bits encontrado`n" -ForegroundColor Green
}

# Passo 5: Criar executável 32 bits (se disponível)
if (-not $Skip32Bit -and (Test-Path $Venv32Path)) {
    Write-Host "🔨 5/8 - Criando executável 32 bits..." -ForegroundColor Yellow
    
    # Limpar build anterior
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    
    & "$Venv32Path\Scripts\python.exe" build_exe.py
    if ($LASTEXITCODE -eq 0 -and (Test-Path "dist\PatientRegistration")) {
        Rename-Item "dist\PatientRegistration" "dist\PatientRegistration-32bit"
        Write-Host "   ✅ Executável 32 bits criado`n" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Falha ao criar executável 32 bits" -ForegroundColor Yellow
        Write-Host "   Continuando apenas com versão 64 bits...`n" -ForegroundColor Yellow
        $Skip32Bit = $true
    }
} else {
    Write-Host "⏭️  5/8 - Executável 32 bits pulado (não disponível)`n" -ForegroundColor Yellow
    $Skip32Bit = $true
}

# Passo 6: Criar estrutura do ZIP
Write-Host "📦 6/8 - Preparando estrutura do pacote..." -ForegroundColor Yellow
New-Item -Path "dist\PatientRegistration" -ItemType Directory -Force | Out-Null

# Copiar versão 64 bits
Copy-Item -Path "dist\PatientRegistration-64bit\*" -Destination "dist\PatientRegistration\" -Recurse
Rename-Item "dist\PatientRegistration\PatientRegistration.exe" "PatientRegistration-64bit.exe"

# Copiar versão 32 bits (se disponível)
if (-not $Skip32Bit -and (Test-Path "dist\PatientRegistration-32bit")) {
    Copy-Item -Path "dist\PatientRegistration-32bit\PatientRegistration.exe" -Destination "dist\PatientRegistration\PatientRegistration-32bit.exe"
}

# Criar README.txt explicativo
$readmeContent = @"
=======================================================================
  Sistema de Solicitação de Cirurgia - Ortopedia Pediátrica
  Versão $Version
=======================================================================

📦 CONTEÚDO DESTE PACOTE:

• PatientRegistration-64bit.exe - Executável para Windows 64 bits
"@

if (-not $Skip32Bit) {
    $readmeContent += @"

• PatientRegistration-32bit.exe - Executável para Windows 32 bits
"@
}

$readmeContent += @"

• Arquivos de suporte e dependências

=======================================================================

🚀 COMO USAR:

1. EXTRAIA TODO O CONTEÚDO desta pasta ZIP
2. EXECUTE o arquivo apropriado para seu sistema:
   
   • Windows 64 bits (recomendado): PatientRegistration-64bit.exe
"@

if (-not $Skip32Bit) {
    $readmeContent += @"

   • Windows 32 bits: PatientRegistration-32bit.exe
"@
}

$readmeContent += @"


3. O sistema abrirá automaticamente no navegador

⚠️ IMPORTANTE:
   - NÃO mova ou delete nenhum arquivo da pasta
   - Mantenha todos os arquivos juntos
   - Para backup, copie a pasta 'instance' que será criada

=======================================================================

📊 INFORMAÇÕES TÉCNICAS:

• Plataforma: Windows 10/11
• Framework: Flask 2.3.3
• Banco de Dados: SQLite 3
• Servidor Web: Waitress 2.1.2

=======================================================================

📚 DOCUMENTAÇÃO:
https://github.com/phgutierrez/patient-registration-system

🐛 REPORTAR PROBLEMAS:
https://github.com/phgutierrez/patient-registration-system/issues

=======================================================================
"@

$readmeContent | Out-File -FilePath "dist\PatientRegistration\README.txt" -Encoding UTF8

Write-Host "   ✅ Estrutura preparada`n" -ForegroundColor Green

# Passo 7: Criar ZIP
Write-Host "📦 7/8 - Comprimindo pacote..." -ForegroundColor Yellow
Compress-Archive -Path "dist\PatientRegistration\*" -DestinationPath $ZipName -Force
$zipSize = (Get-Item $ZipName).Length / 1MB
Write-Host "   ✅ Arquivo ZIP criado ($([math]::Round($zipSize, 2)) MB)`n" -ForegroundColor Green

# Passo 8: Git operations
Write-Host "🏷️  8/8 - Criando tag e enviando para GitHub..." -ForegroundColor Yellow
git add .
git commit -m "Release $TagName - $Message"
git tag -a $TagName -m "$Message"
git push origin teste-exe
git push origin $TagName
Write-Host "   ✅ Tag enviada para o GitHub`n" -ForegroundColor Green

# Resumo final
$exe64Size = (Get-Item "dist\PatientRegistration\PatientRegistration-64bit.exe").Length / 1MB

Write-Host "`n=====================================================================" -ForegroundColor Cyan
Write-Host "  ✅ RELEASE $Version CRIADA COM SUCESSO!" -ForegroundColor Green
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Resumo:" -ForegroundColor Yellow
Write-Host "   Tag criada: $TagName" -ForegroundColor White
Write-Host "   Arquivo ZIP: $ZipName ($([math]::Round($zipSize, 2)) MB)" -ForegroundColor White
Write-Host "   Executável 64 bits: $([math]::Round($exe64Size, 2)) MB" -ForegroundColor White

if (-not $Skip32Bit) {
    $exe32Size = (Get-Item "dist\PatientRegistration\PatientRegistration-32bit.exe").Length / 1MB
    Write-Host "   Executável 32 bits: $([math]::Round($exe32Size, 2)) MB" -ForegroundColor White
}

Write-Host ""
Write-Host "🚀 Próximos passos:" -ForegroundColor Yellow
Write-Host "   1. Acesse a URL que será aberta no navegador" -ForegroundColor White
Write-Host "   2. Arraste o arquivo: $ZipName" -ForegroundColor White
Write-Host "   3. Cole o conteúdo de RELEASE_NOTES_TEMPLATE.md" -ForegroundColor White
Write-Host "   4. Clique em 'Publish release'" -ForegroundColor White
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

# Abrir GitHub releases
Start-Process "https://github.com/phgutierrez/patient-registration-system/releases/new?tag=$TagName"
