[CmdletBinding()]
param(
    [string]$SourceRoot = '',
    [string]$LocalProductRoot = '',
    [string]$SharedDataRoot = '',
    [switch]$PrepareOnly,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ApplicationArguments
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

if ([string]::IsNullOrWhiteSpace($SourceRoot)) {
    $SourceRoot = $PSScriptRoot
}

function Write-Step([string]$Message) {
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success([string]$Message) {
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Get-SafeVersion([string]$Value) {
    $safe = [regex]::Replace($Value, '[^A-Za-z0-9._-]', '_')
    if ([string]::IsNullOrWhiteSpace($safe)) {
        throw 'A versao registrada no build_manifest.json e invalida.'
    }
    return $safe
}

function Get-Sha256([string]$Path) {
    $stream = [System.IO.File]::Open(
        $Path,
        [System.IO.FileMode]::Open,
        [System.IO.FileAccess]::Read,
        [System.IO.FileShare]::Read
    )
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    try {
        $hash = $sha256.ComputeHash($stream)
        return -join ($hash | ForEach-Object { $_.ToString('x2') })
    }
    finally {
        $sha256.Dispose()
        $stream.Dispose()
    }
}

function Read-JsonFile([string]$Path, [string]$Description) {
    try {
        return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    catch {
        throw "Nao foi possivel ler $Description em '$Path': $($_.Exception.Message)"
    }
}

function Ensure-DeploymentManifest([string]$Root) {
    [System.IO.Directory]::CreateDirectory($Root) | Out-Null
    $manifestPath = Join-Path $Root 'deployment.json'

    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        $temporary = Join-Path $Root ('.deployment.' + [guid]::NewGuid().ToString('N') + '.tmp')
        $payload = [ordered]@{
            deployment_id = [guid]::NewGuid().ToString()
            sync_schema_version = 1
            launcher_version = 'network-local-copy-1'
        }
        $payload | ConvertTo-Json | Set-Content -LiteralPath $temporary -Encoding UTF8
        try {
            [System.IO.File]::Move($temporary, $manifestPath)
        }
        catch [System.IO.IOException] {
            Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
            if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
                throw
            }
        }
    }

    $manifest = Read-JsonFile $manifestPath 'o identificador da implantacao'
    $parsedGuid = [guid]::Empty
    if (-not [guid]::TryParse([string]$manifest.deployment_id, [ref]$parsedGuid)) {
        throw "deployment.json nao contem um deployment_id valido: $manifestPath"
    }
    return $parsedGuid.ToString()
}

function Test-LocalDistribution(
    [string]$Destination,
    [string]$ExpectedExecutableHash
) {
    $localExe = Join-Path $Destination 'PatientRegistration.exe'
    $localPython = Join-Path $Destination '_internal\python311.dll'
    $localManifest = Join-Path $Destination 'build_manifest.json'
    if (-not (Test-Path -LiteralPath $localExe -PathType Leaf) -or
        -not (Test-Path -LiteralPath $localPython -PathType Leaf) -or
        -not (Test-Path -LiteralPath $localManifest -PathType Leaf)) {
        return $false
    }
    $actualHash = Get-Sha256 $localExe
    return $actualHash -eq $ExpectedExecutableHash
}

function Copy-Distribution(
    [string]$Source,
    [string]$Destination,
    [string]$ExpectedExecutableHash
) {
    $destinationParent = Split-Path -Parent $Destination
    [System.IO.Directory]::CreateDirectory($destinationParent) | Out-Null
    $lockPath = Join-Path $destinationParent ('.copy-' + (Split-Path -Leaf $Destination) + '.lock')
    $lockStream = $null
    $deadline = [DateTime]::UtcNow.AddSeconds(90)

    while ($null -eq $lockStream -and [DateTime]::UtcNow -lt $deadline) {
        try {
            $lockStream = [System.IO.File]::Open(
                $lockPath,
                [System.IO.FileMode]::OpenOrCreate,
                [System.IO.FileAccess]::ReadWrite,
                [System.IO.FileShare]::None
            )
        }
        catch [System.IO.IOException] {
            Start-Sleep -Milliseconds 350
        }
    }
    if ($null -eq $lockStream) {
        throw 'Outra inicializacao esta copiando o sistema e excedeu 90 segundos.'
    }

    $temporary = $null
    try {
        if (Test-LocalDistribution $Destination $ExpectedExecutableHash) {
            Write-Success 'A versao atual ja esta disponivel neste computador.'
            return
        }

        if (Test-Path -LiteralPath $Destination) {
            Write-Step 'Removendo somente uma copia incompleta da aplicacao (os dados nao serao tocados).'
            Remove-Item -LiteralPath $Destination -Recurse -Force
        }

        $temporary = "$Destination.copy-$PID-$([guid]::NewGuid().ToString('N'))"
        [System.IO.Directory]::CreateDirectory($temporary) | Out-Null
        Write-Step 'Copiando o programa da rede para o perfil local...'

        Copy-Item -LiteralPath (Join-Path $Source 'PatientRegistration.exe') -Destination $temporary
        Copy-Item -LiteralPath (Join-Path $Source 'build_manifest.json') -Destination $temporary

        $internalSource = Join-Path $Source '_internal'
        $internalDestination = Join-Path $temporary '_internal'
        & robocopy.exe $internalSource $internalDestination /E /COPY:DAT /DCOPY:DAT /R:2 /W:1 /NFL /NDL /NJH /NJS /NP
        $robocopyExit = $LASTEXITCODE
        if ($robocopyExit -gt 7) {
            throw "Falha ao copiar a pasta _internal. Codigo do Robocopy: $robocopyExit"
        }

        foreach ($supportFile in @(
            'Iniciar_Sistema_Rede.bat',
            'launcher_network.ps1',
            'LEIA-ME_ACESSO_REDE.txt'
        )) {
            $supportSource = Join-Path $Source $supportFile
            if (Test-Path -LiteralPath $supportSource -PathType Leaf) {
                Copy-Item -LiteralPath $supportSource -Destination $temporary
            }
        }

        if (-not (Test-LocalDistribution $temporary $ExpectedExecutableHash)) {
            throw 'A copia local falhou na validacao de integridade do EXE ou do python311.dll.'
        }

        [System.IO.Directory]::Move($temporary, $Destination)
        $temporary = $null
        Write-Success 'Copia local concluida e validada.'
    }
    finally {
        if ($temporary -and (Test-Path -LiteralPath $temporary)) {
            Remove-Item -LiteralPath $temporary -Recurse -Force -ErrorAction SilentlyContinue
        }
        $lockStream.Dispose()
        Remove-Item -LiteralPath $lockPath -Force -ErrorAction SilentlyContinue
    }
}

try {
    $source = (Resolve-Path -LiteralPath $SourceRoot).Path.TrimEnd('\')
    $sourceExe = Join-Path $source 'PatientRegistration.exe'
    $sourcePython = Join-Path $source '_internal\python311.dll'
    $sourceManifestPath = Join-Path $source 'build_manifest.json'

    foreach ($required in @($sourceExe, $sourcePython, $sourceManifestPath)) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
            throw "Distribuicao incompleta. Arquivo obrigatorio ausente: $required"
        }
    }

    $buildManifest = Read-JsonFile $sourceManifestPath 'o manifesto do build'
    if ([string]$buildManifest.application -ne 'PatientRegistration') {
        throw 'O build_manifest.json nao pertence ao PatientRegistration.'
    }
    $expectedHash = ([string]$buildManifest.executable_sha256).Trim().ToLowerInvariant()
    if ($expectedHash -notmatch '^[0-9a-f]{64}$') {
        throw 'O SHA-256 do executavel no build_manifest.json e invalido.'
    }
    $sourceExeHash = Get-Sha256 $sourceExe
    if ($sourceExeHash -ne $expectedHash) {
        throw 'O EXE da pasta compartilhada nao corresponde ao build_manifest.json. Publique novamente o build completo.'
    }

    if ([string]::IsNullOrWhiteSpace($SharedDataRoot)) {
        $SharedDataRoot = Join-Path $source '_shared_data'
    }
    $deploymentId = Ensure-DeploymentManifest $SharedDataRoot

    if ([string]::IsNullOrWhiteSpace($LocalProductRoot)) {
        if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
            throw 'A variavel LOCALAPPDATA nao esta disponivel neste computador.'
        }
        $LocalProductRoot = Join-Path $env:LOCALAPPDATA 'PatientRegistrationSystem'
    }
    $localProduct = [System.IO.Path]::GetFullPath($LocalProductRoot)
    $manifestHash = (Get-Sha256 $sourceManifestPath).Substring(0, 16)
    $safeVersion = Get-SafeVersion ([string]$buildManifest.version)
    $buildIdentity = "$safeVersion-$manifestHash"
    $localApplication = Join-Path $localProduct "applications\$deploymentId\$buildIdentity"
    $localData = Join-Path $localProduct "data\$deploymentId"
    [System.IO.Directory]::CreateDirectory($localData) | Out-Null

    Copy-Distribution $source $localApplication $expectedHash

    Write-Host "Aplicacao local: $localApplication"
    Write-Host "Dados preservados: $localData"
    Write-Host "Sincronizacao: $SharedDataRoot"

    if ($PrepareOnly) {
        Write-Success 'Preparacao local concluida (modo de verificacao).'
        exit 0
    }

    $env:PRS_LOCAL_RELAUNCHED = '1'
    $env:PRS_DEPLOYMENT_ROOT = $source
    $env:PRS_LOCAL_DATA_ROOT = $localData
    $env:APP_DATA_DIR = $localData
    $env:SYNC_ENABLED = 'true'
    $env:SYNC_ROOT = $SharedDataRoot
    $env:SYNC_INTERVAL_SECONDS = '5'

    $localExe = Join-Path $localApplication 'PatientRegistration.exe'
    Write-Step 'Iniciando o sistema pela copia local...'
    if ($ApplicationArguments -and $ApplicationArguments.Count -gt 0) {
        Start-Process -FilePath $localExe -WorkingDirectory $localApplication -ArgumentList $ApplicationArguments
    }
    else {
        Start-Process -FilePath $localExe -WorkingDirectory $localApplication
    }
    Write-Success 'Sistema iniciado. Esta janela pode ser fechada.'
    exit 0
}
catch {
    Write-Host ''
    Write-Host "[ERRO] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'Nenhum banco ou dado clinico foi removido.' -ForegroundColor Yellow
    exit 1
}
