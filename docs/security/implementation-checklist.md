# Checklist Priorizado de Implementação

Checklist derivado do ESAA e reconciliado com o estado atual do branch.
Os itens marcados como `implemented_pending_verification` não devem ser reabertos como se estivessem intactos; eles já possuem mitigação local e agora precisam de fechamento por teste, regressão e revisão operacional.

## P0

| Item | ESAA | Risco resumido | Status atual | Mudança alvo | Owner | Verificação esperada |
|---|---|---|---|---|---|---|
| Autenticação com senha real e troca obrigatória no primeiro login | `V-001`, `V-002` | Acesso efetivo sem segredo e herança de credenciais previsíveis | `implemented_pending_verification` | Manter o fluxo `especialidade -> solicitante -> senha`, garantir troca obrigatória de senha e impedir qualquer reintrodução de bootstrap com senha fixa | `a definir` | Testar login com senha errada/correta, seed admin, reset de senha e troca obrigatória no primeiro acesso |
| PDFs clínicos fora do `static` público e servidos apenas por rota autenticada | `V-003` | Exposição direta de documentos médicos por URL previsível | `implemented_pending_verification` | Confirmar que novos documentos vão para armazenamento protegido, que links antigos públicos não funcionam e que download/view exigem autenticação e autorização | `a definir` | Verificar `404` em `/static/preenchidos/*`, `403` para acesso cruzado e download/view bem-sucedido para usuário autorizado |
| Escopo por especialidade em pacientes, cirurgias, agenda e APIs | `V-004`, `V-005`, `V-006` | Enumeração de pacientes, agenda anônima e acesso cruzado entre especialidades | `implemented_pending_verification` | Manter consultas e rotas sensíveis sob escopo por especialidade; admin continua com visão total | `a definir` | Testar usuário de especialidade A contra recursos da especialidade B; testar agenda e APIs sem login |
| Sessão endurecida, CSRF restaurado e rate limiting nas rotas críticas | `V-007`, `V-008`, `V-009` | Sequestro de sessão, replay/CSRF e brute force em autenticação/lookup | `implemented_pending_verification` | Validar cookies, timeout, CSRF em confirmação de agenda e throttling em login/consultas | `a definir` | Conferir atributos de cookie, falha de confirmação sem CSRF e bloqueio após rajadas de requests |

## P1

| Item | ESAA | Risco resumido | Status atual | Mudança alvo | Owner | Verificação esperada |
|---|---|---|---|---|---|---|
| Headers HTTP centralizados com baseline mínimo e CSP em `Report-Only` | `V-013` | Navegador sem barreiras mínimas contra clickjacking, sniffing e framing | `implemented_pending_verification` | Centralizar headers em hook global, aplicar `Cache-Control: no-store` onde há dados clínicos/autenticados e manter HSTS sob flag | `a definir` | Validar headers em `/`, `/agenda`, rota protegida de paciente e rota protegida de PDF |
| Dependências vulneráveis atualizadas e `pip-audit` limpo | `V-011` | CVEs conhecidos em pacotes de superfície HTTP | `implemented_pending_verification` | Manter `Werkzeug` na linha 3.1.8 e `requests` em 2.33.1, com atenção ao requisito de Python 3.10+ | `a definir` | Executar `pip-audit`, smoke test de login, agenda, Forms e download de PDF |
| Baseline canônico de configuração e scripts sanitizados | `V-002`, `V-007`, `V-010` | Reintrodução de segredos fracos ou IDs operacionais reais via setup/run docs | `implemented_pending_verification` | Consolidar em `.env.example`, desativar templates legados e remover exemplos sensíveis de scripts/setup | `a definir` | Buscar no repositório por IDs/segredos antigos e validar que `README`/guias apontam só para `.env.example` |
| Logs e mensagens técnicas com higienização/redação mínima | `V-010` | Vazamento de payloads clínicos, detalhes internos e dados pessoais em logs/erros | `in_progress` | Completar revisão de logging, padronizar mensagens genéricas ao usuário e reduzir dados em arquivos locais de log | `a definir` | Revisar logs de geração de PDF, logs de falha de integração e páginas de erro em produção |

## P2

| Item | ESAA | Risco resumido | Status atual | Mudança alvo | Owner | Verificação esperada |
|---|---|---|---|---|---|---|
| Política de retenção, descarte e revogação de documentos | `V-012` | Documentos clínicos podem permanecer indefinidamente sem ciclo de vida definido | `todo` | Definir prazos, gatilhos de descarte, responsável por retenção e procedimento para revogação/remoção segura | `a definir` | Documento operacional aprovado e execução testada em ambiente controlado |
| Minimização de PII em nomes de arquivo, exports e artefatos locais | `V-010`, `V-012` | Nome do paciente em filename e dados clínicos em artefatos locais ampliam exposição | `todo` | Remover PII de nomes físicos de PDFs, revisar exports e padronizar nomenclatura técnica sem dados pessoais | `a definir` | Gerar PDF novo e confirmar ausência de nome do paciente no arquivo persistido |
| Revisão LGPD de integrações externas, rede e estações compartilhadas | `V-012` | Dados acessíveis por share de rede, estações compartilhadas e rotinas de backup sem regra clara | `todo` | Revisar integração Access/UNC, segregação por posto, logout/inatividade e postura de backup/restore | `a definir` | Checklist operacional de estação, rede e backup executado pelo time de implantação |

## P3

| Item | ESAA | Risco resumido | Status atual | Mudança alvo | Owner | Verificação esperada |
|---|---|---|---|---|---|---|
| Rotas operacionais/debug isoladas por admin ou desativadas fora de dev | `V-014` | Funções de shutdown/debug podem ser abusadas por usuários comuns | `todo` | Revisar `shutdown`, heartbeat operacional e quaisquer rotas de diagnóstico para gate administrativo/feature flag | `a definir` | Tentativa de uso por não-admin falha de forma consistente fora de dev |
| Controles de CI segurança | `V-015` | Sem SAST/DAST/secret scan/dependency audit automatizados | `todo` | Criar workflow de CI com `pip-audit`, secret scanning, lint de segurança e smoke checks básicos | `a definir` | Workflow rodando em PR e bloqueando regressões de dependência/segredo |
| Logging estruturado com redaction e request ID | `V-010`, `V-015` | Dificuldade de auditoria sem expor dados sensíveis | `deferred` | Introduzir request ID, mascaramento e trilha mínima de auditoria orientada a incidente | `a definir` | Eventos críticos correlacionáveis sem PII desnecessária |
