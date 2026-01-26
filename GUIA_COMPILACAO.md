# Guia de Compilação - Builds 32 bits e 64 bits

## Visão Geral

Este guia explica como compilar o Sistema de Registro de Pacientes em versões 32 bits e 64 bits usando PyInstaller com servidor Waitress.

## Pré-requisitos

### Software Necessário
- **Python 3.8+** (ou 3.7 para compatibilidade máxima)
- **pip** (gerenciador de pacotes Python)
- **Windows 7+** (para executar os .exe gerados)

### Dependências Python
As seguintes ferramentas serão instaladas automaticamente:
- **PyInstaller** - Empacota Python em executáveis
- **Waitress** - Servidor WSGI para produção
- Todas as dependências do projeto (em requirements.txt)

## Como Compilar

### Opção 1: Script Automático (Recomendado)

#### No Windows:
1. Abra o Prompt de Comando (cmd.exe)
2. Navegue até a pasta do projeto:
   ```bash
   cd C:\Users\seu-usuario\Programacao\patient-registration-system
   ```
3. Execute o script de compilação:
   ```bash
   build_releases.bat
   ```
4. Aguarde a compilação (pode levar alguns minutos)

#### No Linux/Mac:
1. Abra o terminal
2. Navegue até a pasta do projeto:
   ```bash
   cd ~/Programacao/patient-registration-system
   ```
3. Execute:
   ```bash
   python build_releases.py
   ```

### Opção 2: Compilação Manual

#### Instalação de Dependências
```bash
pip install -r requirements.txt
pip install pyinstaller waitress
```

#### Compilar 64 bits
```bash
pyinstaller --distpath dist/64bits --buildpath build_64bits prontuario_64bits.spec
```

#### Compilar 32 bits
```bash
pyinstaller --distpath dist/32bits --buildpath build_32bits prontuario_32bits.spec
```

## Estrutura de Saída

Após a compilação bem-sucedida, a estrutura será:

```
patient-registration-system/
├── dist/
│   ├── 64bits/
│   │   └── prontuario-64bits/
│   │       ├── prontuario-sistema-64bits.exe
│   │       ├── libcrypto-1_1.dll (e outras DLLs)
│   │       ├── src/
│   │       │   ├── templates/
│   │       │   ├── static/
│   │       │   └── database/
│   │       └── ... (outras dependências)
│   │
│   └── 32bits/
│       └── prontuario-32bits/
│           ├── prontuario-sistema-32bits.exe
│           ├── libcrypto-1_1.dll (e outras DLLs)
│           ├── src/
│           │   ├── templates/
│           │   ├── static/
│           │   └── database/
│           └── ... (outras dependências)
│
├── build_64bits/ (pode ser deletado depois)
├── build_32bits/ (pode ser deletado depois)
└── ...
```

## Como Usar os Executáveis

### Execução Simples
Duplo-clique no arquivo `.exe`:
- `prontuario-sistema-64bits.exe` (para Windows 64 bits)
- `prontuario-sistema-32bits.exe` (para Windows 32 bits)

### O que Acontece ao Executar
1. O servidor inicia na porta 5000
2. O navegador padrão abre automaticamente em `http://localhost:5000/login`
3. O sistema está pronto para uso

### Parar o Servidor
- Feche a janela do Prompt de Comando ou
- Pressione `Ctrl+C` no terminal onde o .exe está rodando

## Distribuição

### Preparação para Distribuição

#### 1. Comprimir os Arquivos
```bash
# Windows - Clique com botão direito > Enviar para > Pasta compactada
# Ou use 7-Zip, WinRAR, etc.
```

#### 2. Criar Pastas Separadas
- Crie: `prontuario-v1.0.0-64bits.zip`
  - Contém: `prontuario-64bits/` completo
- Crie: `prontuario-v1.0.0-32bits.zip`
  - Contém: `prontuario-32bits/` completo

#### 3. Incluir Documentação
Em cada .zip, adicione um arquivo `README.txt`:
```
SISTEMA DE REGISTRO DE PACIENTES
Versão 1.0.0

REQUISITOS:
- Windows 7 ou superior
- Porta 5000 disponível
- Aproximadamente 200MB de espaço em disco

COMO EXECUTAR:
1. Extraia o arquivo .zip em um local seguro
2. Duplo-clique em prontuario-sistema-[32bits|64bits].exe
3. Aguarde a inicialização (pode levar alguns segundos)
4. Será aberta automaticamente uma janela do navegador
5. Faça login com suas credenciais

POSSÍVEIS PROBLEMAS:

Porta 5000 em uso:
- Feche outros aplicativos que usem a porta
- Ou edite wsgi.py e recompile com outra porta

Sistema não abre:
- Verifique se a pasta database.db existe
- Tente rodar como Administrador

CONTATO:
Para suporte técnico, contacte o administrador do sistema.
```

### Checklist de Distribuição
- [ ] Versão 64 bits compilada e testada
- [ ] Versão 32 bits compilada e testada
- [ ] Ambas as versões rodando sem erros
- [ ] Pasta de dados (database) incluída
- [ ] Documentação incluída
- [ ] Arquivos compactados corretamente
- [ ] Testado em máquina com sistema 32 bits
- [ ] Testado em máquina com sistema 64 bits

## Troubleshooting

### Erro: "PyInstaller not found"
```bash
pip install pyinstaller
```

### Erro: "Waitress not found"
```bash
pip install waitress
```

### Erro: "Port 5000 already in use"
1. Identifique qual aplicação usa a porta:
   ```bash
   netstat -ano | findstr :5000
   ```
2. Feche o aplicativo ou edite `wsgi.py` para usar outra porta

### Erro: "Database file not found"
Certifique-se de que:
- O arquivo `database.db` está na pasta do .exe
- Ou rode o script de inicialização do banco antes de compilar

### O .exe não abre o navegador
O servidor está rodando, mas o navegador não abriu automaticamente:
1. Abra seu navegador manualmente
2. Vá para: `http://localhost:5000/login`

### Aplicativo muito lento
Possíveis soluções:
- Use a versão 64 bits (melhor desempenho)
- Aumente recursos do sistema
- Verifique se há outras aplicações consumindo recursos

## Customizações

### Mudar Porta Padrão
Edite `wsgi.py`:
```python
serve(app, host='127.0.0.1', port=5001, threads=4)  # Mudar 5000 para 5001
```
Depois recompile.

### Mudar Número de Threads
Edite `wsgi.py`:
```python
serve(app, host='127.0.0.1', port=5000, threads=8)  # Aumentar threads
```
Depois recompile.

### Adicionar Arquivo de Configuração
Se precisar de arquivo `.env` ou configurações especiais:
1. Adicione ao `.spec`:
   ```python
   datas=[
       ('src/templates', 'src/templates'),
       ('src/static', 'src/static'),
       ('src/database', 'src/database'),
       ('.env', '.'),  # Adicionar arquivo de config
   ],
   ```
2. Recompile

## Limpeza Pós-Compilação

Após confirmar que tudo funciona, você pode deletar:
- `build_64bits/` - arquivos temporários
- `build_32bits/` - arquivos temporários
- `*.spec` - se não quiser recompilar depois

Mantenha apenas:
- `dist/` - com as versões compiladas
- `build_releases.py` - para futuras compilações
- `build_releases.bat` - para futuras compilações

## Próximas Compilações

Para compilar uma nova versão:
1. Atualize o código
2. Teste localmente: `python run.py`
3. Execute o script de compilação novamente
4. A versão anterior será sobrescrita em `dist/`

## Mais Informações

- **PyInstaller Docs**: https://pyinstaller.org/
- **Waitress Docs**: https://docs.pylonsproject.org/projects/waitress/
- **Flask Production**: https://flask.palletsprojects.com/deployment/

---

**Última atualização**: 26 de janeiro de 2026
**Versão**: 1.0.0
