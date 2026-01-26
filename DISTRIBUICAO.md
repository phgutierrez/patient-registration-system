# Guia de Distribuição - Patient Registration System

## 📦 O que distribuir

### Mínimo Necessário
```
PatientRegistration.exe     # Executável principal
.env (opcional)             # Configurações
```

### Recomendado
```
PatientRegistration.exe
README.txt                  # Instruções para usuário
.env.example               # Exemplo de configuração
database/                  # Se usar SQLite local
```

## 🚀 Métodos de Distribuição

### 1. ZIP Simples (Mais Fácil)
```bash
# Criar estrutura
mkdir release
copy dist\PatientRegistration.exe release\
copy .env.example release\
echo "Instruções de uso..." > release\README.txt

# Criar ZIP
Compress-Archive -Path release\* -DestinationPath PatientRegistration_v1.0.zip
```

### 2. Instalador com Inno Setup (Profissional)

#### Instalar Inno Setup
- Download: https://jrsoftware.org/isdl.php

#### Script de Instalação (setup.iss)
```ini
[Setup]
AppName=Patient Registration System
AppVersion=1.0
DefaultDirName={pf}\PatientRegistration
DefaultGroupName=Patient Registration
OutputDir=installers
OutputBaseFilename=PatientRegistration_Setup

[Files]
Source: "dist\PatientRegistration.exe"; DestDir: "{app}"
Source: ".env.example"; DestDir: "{app}"; DestName: ".env"

[Icons]
Name: "{group}\Patient Registration"; Filename: "{app}\PatientRegistration.exe"
Name: "{commondesktop}\Patient Registration"; Filename: "{app}\PatientRegistration.exe"

[Run]
Filename: "{app}\PatientRegistration.exe"; Description: "Iniciar aplicação"; Flags: postinstall nowait
```

#### Compilar Instalador
```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup.iss
```

### 3. Portable (USB/Pasta)
```
PatientRegistration_Portable/
├── PatientRegistration.exe
├── config.ini
├── database/
│   └── (banco de dados local)
└── logs/
```

## ⚙️ Configuração para Distribuição

### Arquivo .env.example
```env
# Configuração do Servidor
HOST=127.0.0.1
PORT=5000

# Banco de Dados
DATABASE_URL=sqlite:///patient_registration.db

# Segurança
SECRET_KEY=ALTERAR_PARA_CHAVE_SEGURA

# Logs
LOG_LEVEL=INFO
```

### Arquivo README.txt
```
PATIENT REGISTRATION SYSTEM
===========================

INSTALAÇÃO:
1. Execute PatientRegistration.exe
2. Acesse http://localhost:5000

CONFIGURAÇÃO:
- Edite o arquivo .env para personalizar
- Porta padrão: 5000
- Host padrão: localhost

REQUISITOS:
- Windows 10 ou superior
- Acesso à rede (para banco de dados remoto)

SUPORTE:
- Email: suporte@exemplo.com
```

## 🔒 Segurança

### Antes de Distribuir

1. **Remover Debug**
   - Certifique-se de que `--noconsole` está ativo
   - Não inclua arquivos .pyc ou __pycache__

2. **Variáveis de Ambiente**
   - Nunca distribua .env com senhas reais
   - Use .env.example como modelo

3. **Banco de Dados**
   - Não inclua dados de produção
   - Use banco vazio ou dados de exemplo

4. **Logs**
   - Limpar logs antes de distribuir
   - Configurar nível apropriado

## 📊 Tamanhos de Distribuição

| Método | Tamanho | Complexidade | Profissionalismo |
|--------|---------|--------------|------------------|
| ZIP simples | ~40 MB | Baixa | ⭐⭐ |
| ZIP + Dependências | ~45 MB | Baixa | ⭐⭐⭐ |
| Instalador (Inno) | ~42 MB | Média | ⭐⭐⭐⭐⭐ |
| Portable | ~50 MB | Baixa | ⭐⭐⭐ |

## 🎯 Checklist de Distribuição

### Antes de Criar Pacote
- [ ] Código testado e funcionando
- [ ] Migrations executadas
- [ ] Variáveis sensíveis removidas
- [ ] README com instruções claras
- [ ] Versão documentada

### Empacotamento
- [ ] Executável gerado e testado
- [ ] Arquivo de configuração de exemplo incluído
- [ ] Documentação incluída
- [ ] Arquivos desnecessários removidos

### Após Distribuição
- [ ] Testado em máquina limpa (sem Python)
- [ ] Instalador funciona corretamente
- [ ] Aplicação inicia sem erros
- [ ] Todas as funcionalidades testadas

## 🌐 Distribuição em Rede

### Compartilhar em Rede Local
```batch
# Copiar para pasta compartilhada
xcopy /E /I dist\PatientRegistration.exe \\servidor\shared\apps\

# Criar atalho de rede
# Usuários executam de: \\servidor\shared\apps\PatientRegistration.exe
```

### Servidor Centralizado
```
Servidor (192.168.1.100):
- PatientRegistration.exe (executando como serviço)
- Banco de dados

Clientes:
- Navegador web
- Acesso: http://192.168.1.100:5000
```

## 🔄 Atualizações

### Atualização Manual
1. Substituir .exe antigo pelo novo
2. Manter configurações (.env)
3. Executar migrations se necessário

### Atualização Automática (Avançado)
```python
# Adicionar em server.py
import requests
import os

def check_updates():
    current_version = "1.0.0"
    url = "https://api.example.com/version"
    response = requests.get(url)
    latest = response.json()['version']
    return latest > current_version
```

## 📱 Distribuição por Nível

### Nível 1: Teste Interno
- ZIP simples
- .env com configurações de teste
- Documentação mínima

### Nível 2: Beta/Homologação
- Instalador básico
- Configuração guiada
- Documentação completa
- Suporte limitado

### Nível 3: Produção
- Instalador profissional
- Assinatura digital
- Documentação completa
- Sistema de atualizações
- Suporte técnico

## 🛡️ Assinatura Digital (Opcional)

### Por que assinar?
- Windows não mostra aviso "Publisher Unknown"
- Mais confiável para usuários
- Proteção contra modificações

### Como assinar?
1. Obter certificado de code signing
2. Usar SignTool:
```bash
signtool sign /f certificado.pfx /p senha /t http://timestamp.url PatientRegistration.exe
```

## 📋 Estrutura Completa para Distribuição

```
PatientRegistration_v1.0/
├── PatientRegistration.exe      # Executável principal
├── README.txt                    # Instruções
├── LICENSE.txt                   # Licença
├── .env.example                  # Configuração exemplo
├── CHANGELOG.txt                 # Histórico de versões
└── docs/                         # Documentação adicional
    ├── manual_usuario.pdf
    └── configuracao_avancada.pdf
```

## 🎉 Exemplo de Distribuição Completa

```bash
# Script PowerShell para criar pacote de distribuição

$version = "1.0.0"
$releaseDir = "release_$version"

# Criar estrutura
New-Item -ItemType Directory -Force -Path $releaseDir
Copy-Item "dist\PatientRegistration.exe" $releaseDir
Copy-Item ".env.example" "$releaseDir\.env"
Copy-Item "EXECUTAVEL_README.md" "$releaseDir\README.txt"

# Criar ZIP
Compress-Archive -Path "$releaseDir\*" -DestinationPath "PatientRegistration_v$version.zip"

Write-Host "Pacote criado: PatientRegistration_v$version.zip"
```

## 📞 Suporte ao Usuário Final

### Problemas Comuns

1. **"Não é possível executar"**
   - Verificar antivírus
   - Executar como administrador
   - Verificar permissões

2. **"Erro ao conectar banco"**
   - Verificar .env
   - Testar conexão de rede
   - Verificar firewall

3. **"Porta em uso"**
   - Mudar PORT no .env
   - Verificar processos

### Script de Diagnóstico
Criar `diagnostico.bat`:
```batch
@echo off
echo === Diagnóstico Patient Registration ===
echo.
echo Verificando executável...
if exist PatientRegistration.exe (echo OK) else (echo ERRO: Executável não encontrado)
echo.
echo Verificando configuração...
if exist .env (echo OK) else (echo AVISO: .env não encontrado)
echo.
echo Testando porta 5000...
netstat -an | find "5000"
echo.
pause
```
