# Atualização para a v2.8.0: passo a passo

Esta atualização:
- **não altera o banco de dados** (não há migração);
- **não muda as dependências Python** (`requirements.txt` é o mesmo da v2.7.0);
- não exige recriar o servidor nem parear as estações de novo.

Basta trocar os arquivos do programa.

O que muda (detalhes em [RELEASE_NOTES_2.8.md](../RELEASE_NOTES_2.8.md)):

- exclusão de solicitação de cirurgia, pelo autor ou por um administrador;
- tela **Pendências**, que abre ao clicar no card do início;
- "Minhas próximas cirurgias" no início (a agenda continua com todos os agendamentos);
- formulário de solicitação com obrigatórios marcados, progresso por seção, validação antes do envio, rascunho automático e atalhos;
- correção do build do EXE em máquinas sem Node.js (`app-shell.js`);
- correção do vínculo agenda → solicitação ao marcar Realizada ou Suspensa.

> Os bundles do frontend (`src/static/dist`) já vêm prontos no repositório.
> **Node.js não é necessário** para atualizar nem para gerar o executável.

---

## Qual versão você usa?

| Como o sistema é aberto | Seção |
|---|---|
| `Iniciar_Sistema_Rede.bat` ou `Iniciar_Sistema_Copia_Manual.bat` na pasta compartilhada | [A. Versão em rede](#a-versão-em-rede-pasta-compartilhada) |
| `PatientRegistration.exe` em uma pasta local, em um único computador | [B. Versão local](#b-versão-local-exe-em-um-computador) |
| `run_local.bat`, `run_network.bat` ou `linux/run_*.sh` (instalação Python) | [C. Instalação Python](#c-instalação-python-local-ou-servidor-lan) |

---

## 0. Gerar o executável (uma vez, no computador de build)

Necessário para as seções A e B.

1. Atualize o código: `git pull`, ou baixe o ZIP da versão 2.8.0.
2. Execute `build_exe_32bits.bat`. Não precisa de Node.js: a validação
   estrutural dos scripts foi corrigida nesta versão.
3. Resultado: `dist\Sistema32bits\PatientRegistration\`, com
   `PatientRegistration.exe`, `_internal\`, `build_manifest.json` (versão `2.8.0`),
   os dois BATs, `launcher_network.ps1` e `LEIA-ME_ACESSO_REDE.txt`.

---

## A. Versão em rede (pasta compartilhada)

**Não mexa em:** `_shared_data`, `.env`, `instance`, `logs`, `backup`,
`migration_backup`, `protected_pdfs`.

1. Gere o executável (seção 0).
2. Avise os usuários e evite novas aberturas durante a publicação.
3. Faça backup da pasta compartilhada: pelo menos o EXE, `_internal`,
   `build_manifest.json` e os BATs.
4. Na pasta compartilhada, **substitua** nesta ordem:
   1. `PatientRegistration.exe`;
   2. a pasta `_internal` **inteira** (apague a antiga e copie a nova);
   3. `Iniciar_Sistema_Rede.bat` e `Iniciar_Sistema_Copia_Manual.bat` (só o título mudou para v2.8.0);
   4. `launcher_network.ps1` e `LEIA-ME_ACESSO_REDE.txt`;
   5. **por último**, `build_manifest.json`.
5. Em uma estação de teste, clique em **Encerrar sistema** e abra de novo pelo
   `Iniciar_Sistema_Rede.bat`. O launcher copia a versão 2.8.0 sozinho.
6. Faça a [validação](#validação-após-atualizar) e libere as demais estações.

## B. Versão local (EXE em um computador)

**Não mexa em:** `.env`, `instance\` (banco `prontuario.db`), `logs\`.

1. Gere o executável (seção 0).
2. Clique em **Encerrar sistema**.
3. Faça backup da pasta, ou pelo menos de `instance\` e `.env`.
4. Substitua `PatientRegistration.exe`, a pasta `_internal` **inteira** e
   `build_manifest.json`. Se usa os BATs, substitua-os também.
5. Abra o sistema e faça a [validação](#validação-após-atualizar).

## C. Instalação Python (local ou servidor LAN)

**Não** execute `setup_windows.bat` de novo e não apague `.env` nem `instance`.

1. Pare o sistema.
2. Backup: copie `.env` e `instance\prontuario.db`.
3. Atualize o código:
   - com Git: `git pull`;
   - sem Git: copie os arquivos da v2.8.0 por cima, **exceto** `.env`, `instance`, `logs` e `.venv`.
4. **Não é preciso** rodar `pip install`, porque as dependências não mudaram.
5. Inicie de novo com `run_local.bat` ou `run_network.bat`.
6. No modo LAN, as outras máquinas só precisam recarregar a página.

---

## Validação após atualizar

1. **Início:** o card *Solicitações pendentes* abre **Pendências**. Alterne
   entre *Minhas* e *Todas da especialidade*.
2. **Início:** "Minhas próximas cirurgias" lista só as suas cirurgias, e a
   **Agenda Cirúrgica** continua com todas.
3. **Nova solicitação:**
   - clique em *Gerar solicitação* com o formulário vazio: aparece a lista do que falta;
   - preencha o peso, recarregue a página e veja aparecer *Restaurar rascunho*.
4. **Excluir:**
   - na tela do paciente, a lixeira aparece apenas nas solicitações que você criou (todas, se for admin);
   - confirme a exclusão e veja a solicitação sumir da lista.
5. **Agenda:** marque um evento enviado pelo sistema como *Realizada*. A
   solicitação correspondente deixa de aparecer em Pendências.
6. **Rede:** o indicador de sincronização fica verde. Uma exclusão feita
   numa estação some nas outras após a sincronização.

## Como voltar para a versão anterior

Como o banco não muda, basta restaurar o backup: EXE, `_internal` e
`build_manifest.json`, ou o código no caso da instalação Python.
Solicitações excluídas na v2.8.0 continuam excluídas.
