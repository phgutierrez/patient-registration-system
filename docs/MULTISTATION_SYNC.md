# Execução multiestação e sincronização offline

## Visão geral

O executável pode permanecer em uma pasta compartilhada, mas ele não trabalha
diretamente dessa pasta. Ao ser aberto por UNC ou unidade de rede, o pequeno
launcher copia a versão completa para:

```text
%LOCALAPPDATA%\PatientRegistrationSystem\
├── applications\<deployment_id>\<version>\  # aplicação imutável
└── data\<deployment_id>\                     # dados privados da estação
```

Cada computador mantém seu próprio SQLite em `data\<deployment_id>\instance`.
O sistema recusa um `BASE_DIR` UNC para impedir que o SQLite seja aberto por
várias máquinas. A pasta compartilhada armazena somente a distribuição, o
manifesto e envelopes/checkpoints criptografados.

Esta é uma arquitetura de consistência eventual. Com a pasta acessível, uma
alteração normalmente aparece nas demais estações em até cinco segundos.
Quando a rede falha, o atendimento continua no banco local e a fila é publicada
na reconexão.

## Primeira execução

1. Encerre todas as versões antigas do sistema.
2. Faça uma cópia de segurança da pasta atual.
3. Coloque a distribuição `onedir` completa na pasta compartilhada.
4. Abra o EXE em apenas um computador.
5. O launcher cria `_shared_data\deployment.json`, copia o aplicativo para o
   perfil local e, se houver banco legado, reserva sua migração para essa
   estação.
6. O banco legado é validado com `PRAGMA quick_check` e copiado com a API de
   backup do SQLite. O original não é alterado.
7. A tela exibe uma chave de recuperação. Guarde-a fora dos computadores e
   confirme somente depois de registrar uma cópia segura.

A chave é mostrada em texto apenas na estação inicial. Localmente ela é
protegida pelo Windows DPAPI. Sem a chave e sem uma estação já pareada, os
eventos criptografados não podem ser recuperados.

## Parear outra estação

1. Abra o mesmo EXE compartilhado no novo computador.
2. Aguarde a cópia local.
3. Informe a chave de recuperação na tela de pareamento, sempre no próprio
   computador (`localhost`).
4. O sistema valida a chave contra um verificador autenticado, restaura o
   checkpoint mais recente e aplica os eventos posteriores.

Uma chave incorreta não é gravada no computador. Se o compartilhamento estiver
temporariamente indisponível, uma estação já pareada continua funcionando; uma
estação nova precisa aguardar a rede para concluir o pareamento.

## O que é sincronizado

São sincronizados, por UUID:

- usuários e hashes de PIN;
- pacientes e solicitações;
- especialidade, configurações compartilhadas e procedimentos;
- status da agenda;
- snapshots de documentos;
- versões imutáveis dos dois modelos PDF.

Permanecem locais em cada computador:

- SQLite, `.env`, logs e temporários;
- caminho/configuração do Access;
- cache da agenda;
- identidade da estação e chave protegida pelo DPAPI.

Nenhum PIN em texto claro é sincronizado. Arquivos e cabeçalhos na pasta de
eventos usam apenas UUIDs e metadados operacionais, nunca nomes, CNS ou
prontuários.

## Criptografia, integridade e escrita concorrente

Eventos e checkpoints usam AES-256-GCM. Cada estação grava em seu próprio
diretório, primeiro em arquivo temporário, executa flush e publica por
renomeação atômica. Os eventos possuem sequência e hash anterior. Arquivos
truncados, adulterados, repetidos em outra sequência ou com lacunas interrompem
a sincronização e aparecem no indicador global.

A outbox é criada na mesma transação do dado clínico local. O consumo é
idempotente pelo UUID do evento. Nunca edite ou apague manualmente
`_shared_data`; checkpoints aceleram instalações novas, mas não substituem o
histórico nem o backup.

## Conflitos e histórico

Cada campo possui sua própria versão híbrida (horário, contador lógico,
estação e evento). Portanto, alterações simultâneas em campos diferentes são
combinadas. Quando o mesmo campo muda em duas estações, vence a ordem mais
recente de forma determinística.

- Pacientes com o mesmo prontuário na mesma especialidade são consolidados; o
  anterior vira tombstone e aponta para o registro canônico.
- Em conflito de CNS/CRM de usuário, o valor permanece no vencedor e é removido
  do outro registro.
- Usernames não são trocados pelo usuário; conflitos de implantação recebem
  um sufixo baseado em UUID.

Versões substituídas ficam em **Histórico Sync**, disponível a administradores,
e podem ser restauradas. A restauração gera uma nova alteração sincronizada;
ela não reescreve arquivos antigos.

## Perfil do usuário

Em **Meu Perfil**, qualquer usuário autenticado pode alterar nome completo,
CNS opcional, CRM opcional e PIN. O PIN atual é obrigatório. Novos PINs têm
exatamente seis dígitos. Username, função e especialidade continuam restritos
à administração.

Hashes de senhas antigas permanecem válidos até a próxima alteração. Somente o
hash é enviado nos eventos.

## PDFs históricos

O banco armazena o payload clínico versionado, o usuário emissor, o nome de
download, a versão/hash do modelo e a versão do renderer. Os bytes finais são
gerados em memória com PyMuPDF apenas ao visualizar ou baixar.

Os modelos originais são arquivados uma vez e sincronizados dentro dos
envelopes criptografados. Isso permite regenerar um documento histórico mesmo
depois que a distribuição receber um modelo novo. PDFs gerados não são
persistidos na estação nem na pasta compartilhada. Arquivos legados são
preservados somente no backup da migração.

## Google Forms e resultado incerto

Com a pasta disponível, o envio usa uma trava compartilhada por UUID da
solicitação. Sem rede, o usuário precisa confirmar explicitamente o risco de
duplicidade. Cada tentativa recebe um UUID não clínico.

Uma resposta externa incerta não é repetida automaticamente. A solicitação
fica marcada para revisão; o operador deve conferir o Forms/Calendar antes de
uma nova tentativa.

## Atualização da distribuição

Uma compilação nova produz outro `build_manifest.json`. Ao abrir o EXE da rede,
o launcher copia a versão para outro diretório local. Versões em execução não
são sobrescritas. Banco, identidade, chave e fila continuam no diretório de
dados da implantação.

Não mova somente o `.exe`: publique sempre a pasta `onedir` completa.

## Diagnóstico e recuperação

- Clique no indicador de sincronização para forçar um ciclo.
- `Sincronizado`: sem eventos locais pendentes e último ciclo bem-sucedido.
- `N pendentes`: dados estão seguros localmente, aguardando publicação.
- `Sincronização indisponível`: verifique acesso e permissão de escrita na
  pasta compartilhada; o atendimento local continua.
- Execute `verify_setup.bat` para validar Python, wheels, DPAPI, AES, banco e
  modelos.

Para reconstruir uma estação perdida, remova somente o diretório local daquele
computador, abra novamente a distribuição e faça o pareamento com a chave. O
checkpoint e os eventos recriam o estado. Não use esse procedimento se houver
outbox local ainda não publicada: recupere primeiro o diretório de dados.

Backups institucionais devem abranger a distribuição compartilhada,
`_shared_data` e, periodicamente, os diretórios locais das estações. A
criptografia protege confidencialidade e integridade, mas não substitui backup
contra exclusão do compartilhamento e perda simultânea dos computadores.
