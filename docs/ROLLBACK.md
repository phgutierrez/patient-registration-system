# Rollback operacional

## Pré-cutover
1. Executar `scripts/backup_sqlite.ps1` para snapshot do banco legado.
2. Gerar pacote da versão anterior (executável/scripts Flask).

## Pós-cutover
1. Executar `scripts/dump_postgres.ps1` após a migração inicial.
2. Validar APIs `/api/health`, login e CRUD básico.

## Retorno emergencial
1. Parar containers do novo stack (`docker compose down`).
2. Restaurar pacote da versão Flask anterior.
3. Restaurar `instance/prontuario.db` a partir do backup.
4. Subir serviço legado e validar fluxos clínicos essenciais.
