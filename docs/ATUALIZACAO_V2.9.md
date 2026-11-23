# Atualização para a v2.9.0: passo a passo

Esta atualização:
- **não altera o banco de dados** (não há migração);
- **não muda as dependências Python** (`requirements.txt` é o mesmo da v2.8.0);
- não exige recriar o servidor nem parear as estações de novo.

Basta trocar os arquivos do programa.

O que muda (detalhes em [RELEASE_NOTES_2.9.md](../RELEASE_NOTES_2.9.md)):

- nova tela **Pacientes do dia**, com a agenda do médico logado lida da tabela
  `Ocorrencias` do Access, filtro Manhã/Tarde/Ambos e sincronização a cada 3 min;
- ao clicar no nome do paciente: **Solicitar cirurgia** (importa o paciente do
  CPAM se for preciso) e **Prontuário** (aviso de "em breve");
- **Diagnóstico** e **CID** editáveis no pedido de cirurgia.

> Os bundles do frontend (`src/static/dist`) já vêm prontos no repositório.
> **Node.js não é necessário** para atualizar nem para gerar o executável.

---

## Antes de atualizar (todas as versões)

Confira em **Meu perfil** se o **nome completo** de cada médico corresponde ao
nome usado na agenda do CPAM (coluna `Nome_medico` da tabela `Ocorrencias`).
Pequenas diferenças são toleradas: acentos, "Dr.", "da/de" e uma letra trocada.
Nomes muito diferentes não aparecem na lista.

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

1. Atualize o código: `git pull`, ou baixe o ZIP da versão 2.9.0.
2. Execute `build_exe_32bits.bat`. Não precisa de Node.js.
3. Resultado: `dist\Sistema32bits\PatientRegistration\`, com
   `PatientRegistration.exe`, `_internal\`, `build_manifest.json` (versão `2.9.0`),
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
   3. `Iniciar_Sistema_Rede.bat` e `Iniciar_Sistema_Copia_Manual.bat` (só o título mudou para v2.9.0);
   4. `launcher_network.ps1` e `LEIA-ME_ACESSO_REDE.txt`;
   5. **por último**, `build_manifest.json`.
5. Em uma estação de teste, clique em **Encerrar sistema** e abra de novo pelo
   `Iniciar_Sistema_Rede.bat`. O launcher copia a versão 2.9.0 sozinho.
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
   - sem Git: copie os arquivos da v2.9.0 por cima, **exceto** `.env`, `instance`, `logs` e `.venv`.
     Inclua as pastas novas `src/templates/today` e `src/static/dist`.
4. **Não é preciso** rodar `pip install`, porque as dependências não mudaram.
5. Inicie de novo com `run_local.bat` ou `run_network.bat`.
6. No modo LAN, as outras máquinas só precisam recarregar a página.

---

## Validação após atualizar

1. **Menu lateral:** aparece **Pacientes do dia**. Entre como médico com
   consultas hoje no CPAM.
2. A lista mostra os seus pacientes numerados por ordem de abertura do
   prontuário. Alterne **Manhã / Tarde / Ambos**.
3. Clique em **Sincronizar agora**: o horário "Atualizado às" muda.
4. Clique no nome de um paciente:
   - **Prontuário** mostra o aviso de "ainda não disponível";
   - **Solicitar cirurgia** abre o pedido com os dados do paciente. Se ele não
     existia, passa a aparecer em *Ver Pacientes*.
5. Preencha **Diagnóstico** e **CID**, gere a solicitação e confira o PDF.
6. Se a lista mostrar "nenhuma com médico correspondente", ajuste o nome
   completo do médico em *Meu perfil*.
7. Se aparecer "A tabela Ocorrencias não foi encontrada", confira o arquivo
   Access em *Configurações → Testar conexão*.

## Como voltar para a versão anterior

Como o banco não muda, basta restaurar o backup: EXE, `_internal` e
`build_manifest.json`, ou o código no caso da instalação Python. Os pacientes
importados pela tela Pacientes do dia continuam cadastrados.
