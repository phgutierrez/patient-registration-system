# Atualização para a v2.7.0 — passo a passo

Esta atualização **não altera o banco de dados** (sem migração), **não exige
recriar o servidor**, não exige novo pareamento das estações e não muda a chave
de recuperação. Basta trocar os arquivos do programa.

O que muda na v2.7.0 (detalhes em [CHANGELOG_V2.7.md](CHANGELOG_V2.7.md)):

- interface com HTMX/Alpine/Vite (lista de pacientes e agenda sem recarregar a página);
- faixa verde **"RESERVAR VAGA DE UTI"** no Aviso de Cirurgia quando a reserva de UTI é marcada;
- requisição de hemocomponente sem a data de exemplo do modelo (03/05/2024), sempre com a data de internação;
- correção do botão de menu em telas estreitas;
- `Werkzeug 3.1.9` (alerta de segurança CVE-2026-102598).

> Os bundles do frontend (`src/static/dist`) já vêm prontos no repositório.
> **Node.js não é necessário** para atualizar nem para gerar o executável.

---

## Qual versão você usa?

| Como o sistema é aberto | Seção |
|---|---|
| `Iniciar_Sistema_Rede.bat` ou `Iniciar_Sistema_Copia_Manual.bat` na pasta compartilhada (multiestação) | [A. Versão em rede (pasta compartilhada)](#a-versão-em-rede-pasta-compartilhada) |
| `PatientRegistration.exe` aberto de uma pasta local, em um único computador | [B. Versão local (EXE em um computador)](#b-versão-local-exe-em-um-computador) |
| `run_local.bat`, `run_network.bat` ou `linux/run_*.sh` (instalação Python com `.venv`) | [C. Instalação Python (local ou servidor LAN)](#c-instalação-python-local-ou-servidor-lan) |

---

## 0. Gerar o executável (uma vez, no computador de build)

Necessário para as seções A e B.

1. Atualize o código: `git pull` (ou baixe o ZIP da versão 2.7.0).
2. Execute `build_exe_32bits.bat`.
3. O build valida automaticamente os bundles do frontend, inclui `src/static/dist`
   no `_internal` e roda a autoverificação do executável.
4. Resultado: `dist\Sistema32bits\PatientRegistration\` contendo
   `PatientRegistration.exe`, `_internal\`, `build_manifest.json` (versão `2.7.0`),
   os dois BATs, `launcher_network.ps1` e `LEIA-ME_ACESSO_REDE.txt`.

Se o build parar com "Bundles do frontend ausentes", o checkout está incompleto:
rode `npm ci` e `npm run build` (Node.js 20+) ou baixe novamente o repositório.

---

## A. Versão em rede (pasta compartilhada)

**Não mexa em:** `_shared_data`, `.env`, `instance`, `logs`, `backup`,
`migration_backup`, `protected_pdfs`. As estações **não** precisam ser pareadas
de novo.

1. Gere o executável (seção 0).
2. Avise os usuários e evite novas aberturas durante a publicação (alguns minutos).
   Quem já está com o sistema aberto continua trabalhando na cópia local.
3. Faça backup da pasta compartilhada (pelo menos `PatientRegistration.exe`,
   `_internal`, `build_manifest.json` e os BATs).
4. Na pasta compartilhada, **substitua**:
   1. `PatientRegistration.exe`;
   2. a pasta `_internal` **inteira** (apague a antiga e copie a nova);
   3. `Iniciar_Sistema_Rede.bat` e `Iniciar_Sistema_Copia_Manual.bat` (mudou só o título com a versão);
   4. `launcher_network.ps1` e `LEIA-ME_ACESSO_REDE.txt`;
   5. **por último**, `build_manifest.json`.
5. Em uma estação de teste, feche o sistema (**Encerrar sistema**) e abra de novo
   pelo `Iniciar_Sistema_Rede.bat`. O launcher detecta o novo manifesto e copia a
   versão 2.7.0 para `%LOCALAPPDATA%` automaticamente; os dados locais e a
   sincronização continuam os mesmos.
6. Faça a [validação](#validação-após-atualizar).
7. Libere as demais estações: cada uma recebe a nova versão na próxima vez que
   abrir o sistema pelo BAT.

Estações que usam `Iniciar_Sistema_Copia_Manual.bat` copiado para uma pasta
local: **nada a fazer** — o BAT antigo continua funcionando e busca a versão
nova na pasta de rede. Copiar o BAT novo é opcional (só muda o título).

---

## B. Versão local (EXE em um computador)

**Não mexa em:** `.env`, `instance\` (banco `prontuario.db`), `logs\`.

1. Gere o executável (seção 0).
2. No computador, clique em **Encerrar sistema**.
3. Faça backup da pasta do sistema (ou ao menos de `instance\` e `.env`).
4. Substitua `PatientRegistration.exe`, a pasta `_internal` **inteira** e
   `build_manifest.json`. Se usa os BATs, substitua-os também.
5. Abra o sistema e faça a [validação](#validação-após-atualizar).

---

## C. Instalação Python (local ou servidor LAN)

Vale para `run_local.bat`, `run_network.bat` (servidor LAN clássico) e
`linux/run_local.sh` / `linux/run_network.sh`. **Não** execute
`setup_windows.bat` de novo e não apague `.env`/`instance`.

1. Pare o sistema (Encerrar sistema / feche a janela do `run_network.bat`).
2. Backup: copie `.env` e `instance\prontuario.db`.
3. Atualize o código:
   - com Git: `git pull`
   - sem Git: copie por cima os arquivos da versão 2.7.0 **exceto** `.env`,
     `instance`, `logs`, `.venv`.
4. Atualize as dependências (traz o Werkzeug 3.1.9):
   - Windows: `.venv\Scripts\python.exe -m pip install -r requirements.txt`
   - Linux: `.venv/bin/pip install -r requirements.txt`
5. Inicie de novo (`run_local.bat` ou `run_network.bat`).
6. No modo LAN clássico, as outras máquinas só precisam recarregar a página no
   navegador. Os arquivos novos têm nome com hash, então não é preciso limpar cache.
7. Faça a [validação](#validação-após-atualizar).

---

## Validação após atualizar

1. Entrar com um usuário.
2. **Ver Pacientes**: digitar na busca → a lista atualiza sem recarregar; trocar de página.
3. **Agenda Cirúrgica**: avançar/voltar semana, trocar Semana/Mês, abrir um evento e salvar o status.
4. Abrir/criar uma solicitação com **Reserva de Vaga UTI** marcada → no PDF de
   internação, página "AVISO DE CIRURGIA", aparece a faixa verde
   **RESERVAR VAGA DE UTI** abaixo da data de internação.
5. Solicitação com reserva de sangue → a requisição de hemocomponente mostra a
   **data de internação** (e nunca 03/05/2024).
6. Indicador de sincronização (versão em rede) fica verde.
7. Em tela estreita (celular/janela pequena), o botão de menu (☰) aparece.

> Documentos de solicitações **antigas** são regenerados a partir do conteúdo
> salvo na época (snapshot). Para que uma solicitação antiga ganhe a faixa de UTI
> ou a data corrigida, abra **Editar dados** e salve — isso gera uma nova revisão.

## Como voltar para a versão anterior

Como não há mudança de banco, basta restaurar o backup do passo de backup
(EXE + `_internal` + `build_manifest.json`, ou o código + `pip install -r requirements.txt`).
