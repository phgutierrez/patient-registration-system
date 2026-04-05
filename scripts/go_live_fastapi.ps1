param(
  [switch]$SkipDataMigration = $false
)

Write-Host "[1/6] Backup SQLite legado"
powershell -ExecutionPolicy Bypass -File .\scripts\backup_sqlite.ps1
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[2/6] Infra base"
docker compose up -d --build postgres redis
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[3/6] Alembic upgrade"
docker compose run --rm app alembic upgrade head
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not $SkipDataMigration) {
  Write-Host "[4/6] Migração SQLite -> PostgreSQL"
  docker compose run --rm app python scripts/migrate_sqlite_to_postgres.py
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "[5/6] Subindo app"
docker compose up -d --build app
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[6/6] Health check"
curl http://localhost:8000/api/health
