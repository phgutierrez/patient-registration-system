# Acesso pela rede usando cópia local

## 1. Objetivo

Este procedimento evita o erro:

```text
Error loading Python DLL _internal\python311.dll
Access is denied
```

O Windows pode impedir que uma DLL seja carregada diretamente de um
compartilhamento SMB, mesmo quando o usuário possui permissão de leitura e
execução. O bloqueio ocorre antes de o código Python iniciar. Por isso, abrir
`PatientRegistration.exe` diretamente pela rede não é suportado.

O usuário deve abrir `Iniciar_Sistema_Rede.bat`. O launcher copia a versão da
aplicação para `%LOCALAPPDATA%` e inicia o EXE local, mantendo a sincronização
criptografada na pasta compartilhada.

## 2. O que fica em cada local

### Pasta compartilhada

```text
PatientRegistration\
├── Iniciar_Sistema_Rede.bat       <- arquivo que o usuário deve abrir
├── Iniciar_Sistema_Copia_Manual.bat <- contingência: execute após copiar localmente
├── launcher_network.ps1           <- responsável pela cópia validada
├── LEIA-ME_ACESSO_REDE.txt
├── PatientRegistration.exe
├── build_manifest.json
├── _internal\                     <- bibliotecas e arquivos da aplicação
└── _shared_data\                  <- sincronização: nunca apagar ou substituir
```

### Em cada computador

```text
%LOCALAPPDATA%\PatientRegistrationSystem\
├── applications\<implantação>\<versão>\  <- cópia descartável do programa
└── data\<implantação>\                    <- banco, chave e configuração local
```

Uma atualização cria outra pasta dentro de `applications`. O conteúdo de
`data` não é substituído.

## 3. Preparação da pasta compartilhada

1. Gere o build com `build_exe_32bits.bat`.
2. Ao final, abra a pasta `PatientRegistration` indicada pelo build.
3. Confirme que ela contém:
   - `PatientRegistration.exe`;
   - `build_manifest.json`;
   - `_internal`;
   - `Iniciar_Sistema_Rede.bat`;
   - `Iniciar_Sistema_Copia_Manual.bat`;
   - `launcher_network.ps1`;
   - `LEIA-ME_ACESSO_REDE.txt`.
4. Copie a pasta completa para um compartilhamento no qual os usuários tenham:
   - leitura e execução dos arquivos da aplicação;
   - criação, alteração e renomeação de arquivos em `_shared_data`.
5. Não coloque o SQLite dentro do compartilhamento.
6. Oriente os usuários a criarem um atalho para
   `Iniciar_Sistema_Rede.bat`, nunca para `PatientRegistration.exe`.

O launcher usa somente Windows PowerShell 5.1 e Robocopy, componentes nativos
do Windows. Não exige Python, Visual Build Tools nem privilégio administrativo.

## 4. Primeiro acesso em uma estação

1. Conecte o computador à rede institucional.
2. Abra a pasta compartilhada.
3. Clique duas vezes em `Iniciar_Sistema_Rede.bat`.
4. Aguarde a mensagem `Cópia local concluída e validada`.
5. O navegador será aberto pelo EXE local.
6. Na primeira estação da implantação, conclua a criação/pareamento e guarde a
   chave de recuperação conforme o guia de sincronização.
7. Nas demais estações, informe a chave de recuperação já existente.

Na primeira abertura a cópia pode demorar alguns segundos. Nas seguintes, o
launcher valida o SHA-256 e reutiliza a cópia local da mesma versão.

### Se o Windows não permitir executar o BAT pela rede

Não copie o EXE manualmente e não abra uma cópia local sem as variáveis de
sincronização. Use o modo de contingência:

1. Na pasta compartilhada, copie somente estes dois arquivos para uma pasta
   local, por exemplo a Área de Trabalho:
   - `Iniciar_Sistema_Copia_Manual.bat`;
   - `launcher_network.ps1`.
2. Execute localmente `Iniciar_Sistema_Copia_Manual.bat`.
3. Informe o caminho completo da pasta compartilhada, por exemplo:

   ```text
   \\192.168.1.252\compartilhamento\PatientRegistration
   ```

4. O caminho será validado e salvo somente no perfil daquele usuário em:

   ```text
   %LOCALAPPDATA%\PatientRegistrationSystem\network-source.txt
   ```

5. O helper copiará e validará a aplicação, configurará os diretórios corretos
   de dados/sincronização e iniciará o EXE local.
6. Nos acessos seguintes, execute o mesmo BAT local e pressione `Enter` para
   reutilizar o caminho salvo.

Esse modo existe para políticas que proíbem scripts iniciados por SMB. Ele não
exige copiar manualmente a pasta `_internal` e não cria um banco na rede.

## 5. Acessos seguintes

Use sempre `Iniciar_Sistema_Rede.bat`. O launcher:

1. valida `build_manifest.json` e o SHA-256 do EXE na rede;
2. identifica a implantação compartilhada;
3. verifica se a versão já existe localmente;
4. copia somente quando existe uma versão nova ou a cópia está incompleta;
5. mantém o mesmo diretório local de dados;
6. inicia o EXE da pasta local.

Não copie manualmente apenas o EXE para `%LOCALAPPDATA%`.

## 6. Como publicar uma atualização

Uma atualização do código não exige executar `setup_windows.bat` e não recria
o banco. Passo a passo específico da versão atual: `docs/ATUALIZACAO_V2.7.md`
(v2.7.0 não altera o banco nem exige novo pareamento).

1. Gere e valide o novo build.
2. Evite novos acessos durante os poucos minutos da publicação. As sessões já
   abertas continuam funcionando pela cópia local.
3. Faça backup da pasta compartilhada atual.
4. Preserve integralmente `_shared_data`.
5. Na pasta compartilhada, substitua somente:
   - `PatientRegistration.exe`;
   - `_internal` completa;
   - `Iniciar_Sistema_Rede.bat`;
   - `Iniciar_Sistema_Copia_Manual.bat`;
   - `launcher_network.ps1`;
   - `LEIA-ME_ACESSO_REDE.txt`;
   - `build_manifest.json` (copie por último).
6. Nunca substitua ou apague:
   - `_shared_data`;
   - `.env` legado;
   - `instance` legado;
   - `logs`, `backup`, `migration_backup` ou `protected_pdfs`.
7. Abra `Iniciar_Sistema_Rede.bat` em uma estação de teste.
8. Confirme login, pacientes e indicador de sincronização.
9. Libere o acesso para as demais estações.

O manifesto diferente faz cada estação criar automaticamente uma pasta de
aplicação nova. O banco e a chave continuam em `data\<implantação>`.

## 7. Recuperar uma cópia local incompleta

1. Encerre o sistema naquela estação.
2. Pressione `Win + R`.
3. Abra:

   ```text
   %LOCALAPPDATA%\PatientRegistrationSystem\applications
   ```

4. Remova somente a pasta da versão incompleta dentro de `applications`.
5. Não remova a pasta `data`.
6. Execute novamente `Iniciar_Sistema_Rede.bat`.

O próprio launcher normalmente detecta e substitui uma cópia incompleta.

## 8. Diagnóstico de erros

### Ainda aparece `python311.dll - acesso negado`

Foi aberto o EXE da rede em vez do BAT. Confirme no atalho que o destino termina
em `Iniciar_Sistema_Rede.bat`.

### Erro `Não há suporte para o formato do caminho dado`

Use a versão atual de `launcher_network.ps1`. Ela converte caminhos retornados
como `Microsoft.PowerShell.Core\FileSystem::\\servidor\...` para um UNC nativo
por meio de `ProviderPath` antes de chamar APIs do .NET.

### Controle de Aplicativo Inteligente bloqueou o EXE

Depois de validar o SHA-256, o launcher remove automaticamente a marca
`Zone.Identifier` somente da cópia local. Ele não modifica os arquivos da rede
e não desativa SmartScreen, Smart App Control, AppLocker ou antivírus.

Se o Windows continuar bloqueando o EXE, a causa provável é uma política que
exige assinatura digital ou uma regra de confiança institucional. Nesse caso,
solicite à TI uma regra apropriada ou publique uma versão assinada. Não desative
o Controle de Aplicativo Inteligente: em alguns computadores ele não pode ser
reativado sem redefinir o Windows.

### PowerShell bloqueado

O BAT mostra que `powershell.exe` não foi encontrado ou não pôde ser iniciado.
Solicite à TI a liberação do Windows PowerShell para esse launcher. Não é
necessário liberar scripts globalmente: o BAT usa `-ExecutionPolicy Bypass`
somente no processo atual.

### Falha ao criar `_shared_data`

O usuário precisa de permissão de criação, escrita e renomeação nessa pasta.
Permissão apenas de leitura não permite sincronização.

### SHA-256 não corresponde

O EXE e o `build_manifest.json` pertencem a builds diferentes ou a publicação
foi interrompida. Publique novamente o EXE, `_internal` e, por último, o
manifesto do mesmo build.

### Robocopy retorna erro

Verifique espaço livre em `%LOCALAPPDATA%`, estabilidade da rede e bloqueios do
antivírus. O launcher tenta a cópia novamente sem tocar nos dados.

### Sincronização indisponível após iniciar

Confirme acesso de leitura/escrita em `_shared_data` e consulte
`MULTISTATION_SYNC.md`. A aplicação local pode continuar atendendo e publicará
as alterações quando a rede voltar.

## 9. Segurança e backup

- Não desative antivírus, SmartScreen, AppLocker ou WDAC.
- Não abra um SQLite diretamente pela rede.
- Não compartilhe a chave de recuperação fora da equipe autorizada.
- Faça backup de `_shared_data` e dos diretórios locais `data`.
- A pasta `applications` é apenas cache de executáveis e pode ser reconstruída.
- A pasta `data` contém dados importantes e não deve ser apagada durante uma
  atualização.

Para detalhes sobre pareamento, criptografia e recuperação, consulte
`MULTISTATION_SYNC.md`.
