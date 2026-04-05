param(
  [string]$Host = 'localhost',
  [string]$Port = '5432',
  [string]$User = 'postgres',
  [string]$Database = 'patient_registration',
  [string]$TargetDir = 'backups/postgres'
)

New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$target = Join-Path $TargetDir "patient_registration_$timestamp.sql"
pg_dump -h $Host -p $Port -U $User -d $Database -f $target
Write-Output "Dump criado: $target"
