# Atualização para a v3.0.0: passo a passo

Esta atualização:
- **não altera o banco de dados** (não há migração);
- **não muda as dependências Python** (`requirements.txt` é o mesmo da v2.9.0);
- não exige recriar o servidor nem parear as estações de novo.

Basta trocar os arquivos do programa.

O que muda (detalhes em [RELEASE_NOTES_3.0.md](../RELEASE_NOTES_3.0.md)):

- nova tela **Controle de Cirurgias**, exclusiva para administradores e somente
  leitura, com calendário mensal/semanal, indicadores, lista filtrável e resumo
  dos motivos de cancelamento, lida das tabelas `Ocorrencias_SS`,
  `tb_procedimentos_BC` e `tb_registro_bC` do Access.

> Os bundles do frontend (`src/static/dist`) já vêm prontos no repositório.
> **Node.js não é necessário** para atualizar nem para gerar o executável.

---

## Antes de atualizar (todas as versões)

Confirme que o Access configurado em *Configurações → Testar conexão* é o banco
que contém as tabelas `Ocorrencias_SS`, `tb_procedimentos_BC` e `tb_registro_bC`.
Apenas usuários **administradores** veem a nova tela.

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

1. Atualize o código: `git pull`, ou baixe o ZIP da versão 3.0.0.
2. Execute `build_exe_32bits.bat`. Não precisa de Node.js.
3. Resultado: `dist\Sistema32bits\PatientRegistration\`, com
   `PatientRegistration.exe`, `_internal\`, `build_manifest.json` (versão `3.0.0`),
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
   3. `Iniciar_Sistema_Rede.bat` e `Iniciar_Sistema_Copia_Manual.bat` (só o título mudou para v3.0.0);
   4. `launcher_network.ps1` e `LEIA-ME_ACESSO_REDE.txt`;
   5. **por último**, `build_manifest.json`.
5. Em uma estação de teste, clique em **Encerrar sistema** e abra de novo pelo
   `Iniciar_Sistema_Rede.bat`. O launcher copia a versão 3.0.0 sozinho.
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
   - sem Git: copie os arquivos da v3.0.0 por cima, **exceto** `.env`, `instance`, `logs` e `.venv`.
     Inclua as pastas novas `src/templates/surgery_control`, `src/static/dist` e `src/static/icons`.
4. **Não é preciso** rodar `pip install`, porque as dependências não mudaram.
5. Inicie de novo com `run_local.bat` ou `run_network.bat`.
6. No modo LAN, as outras máquinas só precisam recarregar a página (Ctrl+F5).

---

## Validação após atualizar

1. Entre como **administrador**: o menu lateral mostra **Controle de Cirurgias**.
2. Entre como médico comum: o item **não** aparece e abrir
   `/controle-cirurgias/` diretamente mostra "acesso negado".
3. Na tela, alterne **Mensal / Semanal**, use *anterior*, *próximo* e *Hoje*
   (a semana começa na segunda-feira) e clique em um dia do calendário.
4. Confira os indicadores (canceladas, realizadas, sem resposta do bloco), o filtro por
   status e a busca por paciente/prontuário.
5. Em uma cirurgia cancelada, confira o grupo e a descrição do motivo. Casos sem
   correspondência mostram "Motivo não localizado"; casos duplicados mostram
   "Vínculo ambíguo"; se o registro do bloco (`Situaçao`) diz REALIZADA, mostram
   "Divergência".
6. Se aparecer aviso de cirurgias sem data programada, use **Ver lista**.
7. Se aparecer erro de tabela ou colunas, confira o arquivo em
   *Configurações → Testar conexão* e as tabelas citadas acima.
   Avisos sobre procedimentos ou suspensões indisponíveis indicam que
   `tb_procedimentos_BC` ou `tb_registro_bC` não foram lidas.

## Como voltar para a versão anterior

Como o banco não muda, basta restaurar o backup: EXE, `_internal` e
`build_manifest.json`, ou o código no caso da instalação Python.
