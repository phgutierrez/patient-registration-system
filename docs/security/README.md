# Segurança do Repositório

Este diretório concentra o baseline atual de segurança do `patient-registration-system`.
A ideia é manter aqui o que já foi mitigado no branch, o que ainda precisa de validação e o backlog residual que não deve se perder entre rodadas de correção.

## Documentos deste pacote

- [implementation-checklist.md](implementation-checklist.md): checklist priorizado, reconciliado com os achados ESAA e com o estado atual do branch.
- [lgpd-document-handling-pass.md](lgpd-document-handling-pass.md): segunda passada focada em exposição LGPD/privacidade e ciclo de vida documental.
- [http-headers-and-deps-pass.md](http-headers-and-deps-pass.md): segunda passada focada em headers HTTP, CSP/HSTS e atualização de dependências vulneráveis.
- [admin-bootstrap-guide.md](admin-bootstrap-guide.md): guia curto de operação para `ADMIN_BOOTSTRAP_*`.

## Status usados neste pacote

- `todo`: ainda não iniciado.
- `in_progress`: há trabalho em andamento, mas ainda incompleto.
- `implemented_pending_verification`: mudança já existe no branch, mas precisa de verificação funcional/regressão antes de ser dada como fechada.
- `done`: implementado e validado no escopo atual.
- `deferred`: conhecido, aceito temporariamente fora do escopo imediato.

## Como ler o checklist

1. Comece por `P0`: itens de bloqueio de release ou de superfície clínica direta.
2. Passe para `P1`: endurecimento de navegador, dependências, configuração e bootstrap.
3. Use `P2` para fechar lacunas de LGPD/documentos.
4. Mantenha `P3` como backlog estruturado de médio prazo.

## Material-fonte utilizado

Este pacote foi consolidado a partir dos artefatos ESAA externos ao repositório e do estado corrente do branch local.
Os artefatos usados como insumo foram:

- `/Users/pedrofreitas/Programacao/esaa-security/reports/final/security-audit-report.md`
- `/Users/pedrofreitas/Programacao/esaa-security/reports/phase4/executive-summary.md`
- `/Users/pedrofreitas/Programacao/esaa-security/reports/phase4/technical-remediations.md`
- `/Users/pedrofreitas/Programacao/esaa-security/reports/phase4/best-practices.md`

Os documentos daqui precisam continuar úteis mesmo sem acesso a esses arquivos externos.

## Regras práticas daqui para frente

- Use apenas `.env.example` como template ativo.
- Não reintroduza IDs operacionais reais, URLs reais de formulário ou segredos fixos em scripts/examples.
- Qualquer finding já mitigado em código deve continuar no checklist como `implemented_pending_verification` até passar por verificação explícita.
- Mudanças de segurança com impacto de compatibilidade devem atualizar scripts, docs e requisitos na mesma PR.
