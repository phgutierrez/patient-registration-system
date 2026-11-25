# Atualização para a v3.0.1: passo a passo

Esta atualização:
- **não altera o banco de dados** (não há migração);
- **não muda as dependências Python** (`requirements.txt` é o mesmo da v3.0.0);
- não exige recriar o servidor nem parear as estações de novo;
- cria sozinha a pasta `instance\access_cache` (cópia local do Access) quando necessário.

Basta trocar os arquivos do programa.

O que muda (detalhes em [RELEASE_NOTES_3.0.1.md](../RELEASE_NOTES_3.0.1.md)):

- a tela **Controle de Cirurgias** abre na hora e lê o Access em segundo plano
  (antes ficava girando e podia derrubar a conexão);
- leitura filtrada (12 meses por padrão), com cópia local do `.accdb` no modo rede;
- botão **Atualizar agora** e **Tentar novamente**.

> Os bundles do frontend (`src/static/dist`) já vêm prontos no repositório.
> **Node.js não é necessário** para atualizar nem para gerar o executável.

---

## Antes de atualizar (todas as versões)

- Confirme que o computador que roda o servidor tem espaço livre em disco para uma
  cópia do arquivo Access (o dobro do tamanho do `.accdb`, até 500 MB por padrão).
- Para desligar a cópia local, acrescente `SURGERY_LOCAL_COPY=0` ao `.env`
  (veja as demais variáveis nas notas de versão).

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

1. Atualize o código: `git pull`, ou baixe o ZIP da versão 3.0.1.
2. Execute `build_exe_32bits.bat`. Não precisa de Node.js.
3. Resultado: `dist\Sistema32bits\PatientRegistration\`, com
   `PatientRegistration.exe`, `_internal\`, `build_manifest.json` (versão `3.0.1`),
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
   3. `Iniciar_Sistema_Rede.bat` e `Iniciar_Sistema_Copia_Manual.bat` (só o título mudou para v3.0.1);
   4. `launcher_network.ps1` e `LEIA-ME_ACESSO_REDE.txt`;
   5. **por último**, `build_manifest.json`.
5. Em uma estação de teste, clique em **Encerrar sistema** e abra de novo pelo
   `Iniciar_Sistema_Rede.bat`. O launcher copia a versão 3.0.1 sozinho.
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
   - sem Git: copie os arquivos da v3.0.1 por cima, **exceto** `.env`, `instance`, `logs` e `.venv`.
     Inclua `src/services`, `src/templates/surgery_control`, `src/static/dist` e `src/static/icons`.
4. **Não é preciso** rodar `pip install`, porque as dependências não mudaram.
5. Inicie de novo com `run_local.bat` ou `run_network.bat`.
6. No modo LAN, as outras máquinas só precisam recarregar a página (Ctrl+F5).

---

## Validação após atualizar

1. Entre como **administrador** e abra **Controle de Cirurgias**. A página deve abrir
   **na hora**, mostrando *Carregando as cirurgias…* com a etapa e o tempo.
2. Enquanto carrega, abra **Pacientes do dia** em outra aba: deve continuar respondendo.
3. Quando terminar, a tela troca sozinha para o calendário e os indicadores. Anote
   quanto tempo levou a primeira carga.
4. Recarregue a página: os dados aparecem imediatamente (última leitura).
5. Clique em **Atualizar agora**: aparece "Atualizando em segundo plano" e os dados
   trocam quando a leitura termina.
6. Navegue para um mês de mais de 12 meses atrás: aparece "Carregando o período anterior".
7. No modo rede, confirme que existe `instance\access_cache\cirurgias_*.accdb`.
   Se aparecer o aviso "Cópia local indisponível", a leitura foi feita direto pela rede
   (confira espaço em disco e permissões da pasta `instance`).
8. Se a carga ainda demorar muito, envie ao suporte as linhas do log que começam com
   `Cirurgias etapa=` e `Cópia local do Access` (não contêm dados de pacientes).

## Como voltar para a versão anterior

Como o banco não muda, basta restaurar o backup: EXE, `_internal` e
`build_manifest.json`, ou o código no caso da instalação Python. A pasta
`instance\access_cache` pode ser apagada com segurança.
