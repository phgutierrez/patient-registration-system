param(
  [string]$Source = 'instance/prontuario.db',
  [string]$TargetDir = 'backups/sqlite'
)

New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$target = Join-Path $TargetDir "prontuario_$timestamp.db"
Copy-Item $Source $target -Force
Write-Output "Backup criado: $target"
