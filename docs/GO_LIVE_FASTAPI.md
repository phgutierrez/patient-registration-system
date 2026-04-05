# Go-live FastAPI + React (Windows Server)

## 1) Pré-requisitos
- Docker Desktop ou Docker Engine com Compose habilitado.
- Porta 8000 liberada no firewall interno.
- Arquivo `.env` preenchido a partir de `.env.example.modernizacao`.

## 2) Backup pré-corte (SQLite legado)
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\backup_sqlite.ps1
```

## 3) Subir infraestrutura nova (PostgreSQL + Redis + App)
```powershell
docker compose up -d --build postgres redis
```

## 4) Aplicar migrações no PostgreSQL
```powershell
docker compose run --rm app alembic upgrade head
```

## 5) Migrar dados do SQLite para PostgreSQL (one-shot)
```powershell
docker compose run --rm app python scripts/migrate_sqlite_to_postgres.py
```

## 6) Subir aplicação completa
```powershell
docker compose up -d --build app
```

## 7) Smoke checks
```powershell
# Health API
curl http://localhost:8000/api/health

# OpenAPI
curl http://localhost:8000/openapi.json
```

## 8) Dump pós-corte (estado inicial PostgreSQL)
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\dump_postgres.ps1
```

## 9) Rollback emergencial
1. `docker compose down`
2. Restaurar pacote legado Flask.
3. Restaurar `instance/prontuario.db` do backup.
4. Subir stack legado e validar fluxos clínicos.
