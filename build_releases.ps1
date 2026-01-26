# ============================================================================
# Script de Compilação v1.0.1 - Prontuário de Pacientes
# Plataforma: Windows PowerShell
# Requerimentos: Python 3.11+, PyInstaller, Waitress
# ============================================================================

param(
    [switch]$Skip64bit = $false,
    [switch]$Skip32bit = $false,
    [string]$Version = "v1.0.1"
)

Write-Host "============================================================================"
Write-Host "  Compilador PowerShell - Sistema de Registro de Pacientes $Version"
Write-Host "============================================================================"
Write-Host ""

# Verificar Python
Write-Host "[1/5] Verificando Python..."
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Python não encontrado" -ForegroundColor Red
    exit 1
}
Write-Host "  ✓ $pythonVersion"

# Verificar PyInstaller
Write-Host "[2/5] Verificando PyInstaller..."
$pipShow = pip show PyInstaller 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ! PyInstaller não instalado, instalando..."
    pip install "PyInstaller>=6.10.0"
}
Write-Host "  ✓ PyInstaller pronto"

# Verificar Waitress
Write-Host "[3/5] Verificando Waitress..."
$waitress = pip show waitress 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ! Waitress não instalado, instalando..."
    pip install waitress==2.1.2
}
Write-Host "  ✓ Waitress pronto"
Write-Host ""

# Compilar 64 bits
if (-not $Skip64bit) {
    Write-Host "[4a/5] Compilando versão 64-bits..."
    Write-Host "       (Isto pode levar 10-15 minutos)"
    Write-Host ""
    
    pyinstaller --clean prontuario_64bits.spec
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Build 64-bits compilado com sucesso"
    } else {
        Write-Host "  ✗ ERRO na compilação 64-bits" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[4a/5] Pulando compilação 64-bits (conforme solicitado)"
}
Write-Host ""

# Compilar 32 bits
if (-not $Skip32bit) {
    Write-Host "[4b/5] Compilando versão 32-bits..."
    Write-Host "       (Isto pode levar 10-15 minutos)"
    Write-Host ""
    
    pyinstaller --clean prontuario_32bits.spec
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Build 32-bits compilado com sucesso"
    } else {
        Write-Host "  ✗ ERRO na compilação 32-bits" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[4b/5] Pulando compilação 32-bits (conforme solicitado)"
}
Write-Host ""

# Criar ZIPs
Write-Host "[5/5] Criando arquivos ZIP..."

Push-Location dist

if (-not $Skip64bit) {
    Write-Host "  Compactando 64-bits..."
    if (Test-Path "prontuario-$Version-64bits.zip") {
        Remove-Item "prontuario-$Version-64bits.zip" -Force
    }
    Compress-Archive -Path "64bits/prontuario-64bits" -DestinationPath "prontuario-$Version-64bits.zip" -Force
    
    $size = (Get-Item "prontuario-$Version-64bits.zip").Length / 1MB
    Write-Host "  ✓ prontuario-$Version-64bits.zip ($([Math]::Round($size, 1)) MB)"
}

if (-not $Skip32bit) {
    Write-Host "  Compactando 32-bits..."
    if (Test-Path "prontuario-$Version-32bits.zip") {
        Remove-Item "prontuario-$Version-32bits.zip" -Force
    }
    Compress-Archive -Path "32bits/prontuario-32bits" -DestinationPath "prontuario-$Version-32bits.zip" -Force
    
    $size = (Get-Item "prontuario-$Version-32bits.zip").Length / 1MB
    Write-Host "  ✓ prontuario-$Version-32bits.zip ($([Math]::Round($size, 1)) MB)"
}

Pop-Location

Write-Host ""
Write-Host "============================================================================"
Write-Host "  ✓ COMPILAÇÃO CONCLUÍDA COM SUCESSO!"
Write-Host "============================================================================"
Write-Host ""
Write-Host "  Arquivos de Release:"
Write-Host "  - dist/prontuario-$Version-64bits.zip"
Write-Host "  - dist/prontuario-$Version-32bits.zip"
Write-Host ""
Write-Host "  Próximas Etapas:"
Write-Host "  1. Teste os executáveis:"
Write-Host "     dist\64bits\prontuario-64bits\prontuario-64bits.exe"
Write-Host "     dist\32bits\prontuario-32bits\prontuario-32bits.exe"
Write-Host ""
Write-Host "  2. Faça upload dos ZIPs para GitHub Release:"
Write-Host "     https://github.com/phgutierrez/patient-registration-system/releases/new"
Write-Host ""
Write-Host "  3. Selecione tag: $Version"
Write-Host "  4. Arraste os 2 arquivos .zip"
Write-Host "  5. Clique em 'Publish release'"
Write-Host ""
