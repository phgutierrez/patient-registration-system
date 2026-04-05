# Segunda Passada: LGPD, Privacidade e Tratamento de Documentos

Este documento foca somente em exposição de dados pessoais/sensíveis e no ciclo de vida documental.
Ele serve como insumo técnico-operacional, não como parecer jurídico.

> Nota importante: este material **não é assessoria jurídica**. Ele traduz riscos técnicos e operacionais para apoiar decisões de conformidade e implantação.

## Achados

| ID | Tema | Exposição observada | Estado atual no branch | Risco | Ação prioritária |
|---|---|---|---|---|---|
| `LGPD-01` | Inventário de dados | O sistema processa nome, data de nascimento, CNS, endereço, contato, diagnóstico, CID, dados clínicos e agenda cirúrgica | Parcialmente conhecido em modelos/rotas; sem inventário formal publicado | Alto | Formalizar inventário por origem, finalidade, base de retenção e operador responsável |
| `LGPD-02` | PDFs gerados | PDFs clínicos foram tirados do `static` público, mas o armazenamento local protegido ainda faz parte da superfície de risco | Melhorado: acesso web protegido | Alto | Definir política de retenção, descarte, backup e auditoria de acesso aos PDFs |
| `LGPD-03` | Nomes de arquivo | O nome físico do PDF ainda carrega identificadores clínicos e o nome do paciente | Não mitigado nesta passada | Alto | Remover PII do filename persistido; usar UUID/ID interno + metadados no banco |
| `LGPD-04` | Artefatos locais | Banco SQLite, diretório `instance/`, PDFs protegidos e `pdf_generation.log` permanecem locais no host | Parcialmente mitigado | Alto | Restringir permissões de pasta, revisar logs e definir backup/restauração com acesso mínimo |
| `LGPD-05` | Logs e erros | Há melhora em mensagens de erro ao usuário, mas ainda falta revisão de payloads e trilhas locais de integração/geração | Em progresso | Médio/alto | Reduzir PII em logs, padronizar redaction e eliminar dumps desnecessários |
| `LGPD-06` | Exports / cópias manuais | Banco SQLite, PDFs e possíveis exports podem ser copiados fora do sistema sem trilha de controle | Não formalizado | Alto | Definir rotina controlada de exportação, cópia e restauração com responsável designado |
| `LGPD-07` | Share de rede / Access DB | Integração opcional com banco Access em UNC path (`\\192.168.1.252\...`) depende de postura externa ao app | Não mitigado | Alto | Validar ACLs do share, conta técnica usada, logging de acesso e necessidade real da integração |
| `LGPD-08` | Retenção e descarte | Não há regra documentada de retenção para PDFs, logs locais e backups | Não mitigado | Alto | Criar matriz de retenção/descarte e procedimento de eliminação segura |
| `LGPD-09` | Revogação / correção | Não há rotina operacional explícita para correção, substituição ou revogação de documentos já gerados | Não mitigado | Médio | Definir procedimento de reemissão, revogação lógica e remoção física quando cabível |
| `LGPD-10` | Least privilege | O app evoluiu para escopo por especialidade, mas a implantação ainda precisa refletir isso em host, backups e compartilhamentos | Melhorado no app; incompleto na operação | Médio/alto | Garantir privilégios mínimos também em sistema operacional, compartilhamentos e banco auxiliar |
| `LGPD-11` | Estações compartilhadas | Em ambiente hospitalar multiusuário, sessão de navegador, cache local e downloads podem vazar entre operadores | Parcialmente mitigado com sessão e auth | Médio/alto | Padronizar logout, bloqueio de tela, perfis de navegador e limpeza de downloads em postos compartilhados |
| `LGPD-12` | Backup e recuperação | Há instruções de backup, mas não uma política de criptografia, guarda, retenção e teste de restauração | Não mitigado | Médio/alto | Definir RPO/RTO, criptografia, responsável e rotina de teste de restore |

## Inventário técnico resumido

| Superfície | Exemplos | Observação de privacidade |
|---|---|---|
| Banco local | `instance/prontuario.db` | Contém dados pessoais e clínicos estruturados |
| Documentos gerados | `instance/protected_pdfs/*` | Conteúdo clínico sensível; precisa ciclo de vida definido |
| Logs locais | `pdf_generation.log` e stdout/stderr operacionais | Exigem revisão de redaction e retenção |
| Navegador / estação | sessão autenticada, downloads, abas abertas | Importante em computadores compartilhados |
| Integração externa | Google Calendar, Google Forms, Access/UNC | Exige revisão de necessidade, acesso e minimização |
| Backups / cópias | SQLite, PDFs, exports manuais | Sem política consolidada no repositório |

## Checklist de remediação LGPD/documentos

- [ ] Remover nome do paciente do filename físico dos PDFs gerados.
- [ ] Definir prazo de retenção para PDFs, banco local, logs e backups.
- [ ] Formalizar procedimento de eliminação segura e reemissão de documentos.
- [ ] Revisar `pdf_generation.log` e demais logs locais para remover PII desnecessária.
- [ ] Restringir permissões do diretório `instance/` e do host que armazena PDFs.
- [ ] Revisar a integração com Access em share de rede sob ótica de ACL, credencial e necessidade mínima.
- [ ] Padronizar conduta para estações compartilhadas: logout, bloqueio de tela, limpeza de downloads e navegador.
- [ ] Documentar quem pode exportar/copiar banco e documentos, em que contexto e com qual trilha.
- [ ] Definir política de backup com criptografia, retenção, restore periódico e responsável.
- [ ] Publicar um inventário de dados por finalidade e fluxo operacional.

## Leituras operacionais recomendadas para a próxima rodada

- Política interna de retenção e descarte do hospital/clínica.
- Inventário de ativos do host onde ficam `instance/` e backups.
- Procedimentos do time local para computador compartilhado, antivírus e backups.
