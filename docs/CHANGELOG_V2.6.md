# Changelog — v2.6

Data: julho de 2026

## Multiestação offline-first

- O EXE aberto de UNC/unidade de rede agora copia a distribuição imutável para
  `%LOCALAPPDATA%` e usa um SQLite privado por computador.
- Alterações são registradas em outbox transacional e sincronizadas por
  envelopes AES-256-GCM, sequência, hash anterior e publicação atômica.
- Foram adicionados pareamento por chave de recuperação, proteção DPAPI,
  checkpoints, indicador global, sincronização manual e histórico restaurável.
- Conflitos são resolvidos por campo com ordenação híbrida; exclusões usam
  tombstones versionados.
- Configuração do Access e cache da agenda permanecem específicos da estação.

## Usuários e documentos

- Nova página **Meu Perfil** para alterar nome, CNS, CRM e PIN mediante PIN
  atual.
- PDFs passaram a ser regenerados em memória a partir de snapshots versionados.
- Modelos PDF históricos são arquivados e sincronizados de forma criptografada;
  PDFs finais não são persistidos.
- Envios ao Google Forms usam trava compartilhada por solicitação e registram
  tentativas de resultado incerto sem repetição automática.

## Setup e build

- Adicionado `PyCryptodome==3.23.0` e wheel win32 versionado com SHA-256.
- Setup e build continuam aceitando somente wheels binários, sem Visual Build
  Tools nem privilégios administrativos.
- O verificador testa AES-GCM, DPAPI, novas tabelas, modelos PDF e dependências.
- Build `onedir` 32-bit validado com 807 arquivos e 66,39 MiB.

## Qualidade

- Corrigida uma falha detectada no self-check real do servidor: import ausente
  do serviço de sincronização em `initialize_app()`.
- Adicionados testes de duas estações, chave incorreta, adulteração, checkpoint,
  merge por campo, tombstones, launcher local, perfil, snapshots e self-check.
- Suíte final: 101 testes aprovados.

Consulte [MULTISTATION_SYNC.md](MULTISTATION_SYNC.md) antes de migrar uma pasta
com dados existentes.
