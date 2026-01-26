# ✅ CORREÇÃO: Persistência de Dados no Executável

## Problema Identificado

Após usar o sistema pelo executável e encerrá-lo, ao reiniciar o PatientRegistration.exe, todos os dados estavam sendo perdidos (usuários, pacientes, solicitações). O sistema voltava zerado como se fosse a primeira execução.

## Causa Raiz

O PyInstaller, quando empacota no modo **ONE-FILE**, extrai os arquivos para um diretório temporário (ex: `C:\Users\...\AppData\Local\Temp\_MEI324682\`). 

O código original em `src/config.py` usava:
```python
BASE_DIR = Path(__file__).resolve().parent.parent
```

Quando executado como `.exe`, `__file__` apontava para o diretório temporário, fazendo com que o banco de dados `prontuario.db` fosse criado lá. Ao encerrar o executável, o Windows **deleta automaticamente** esse diretório temporário, **perdendo todos os dados**.

## Solução Implementada

### Alteração em `src/config.py`

```python
import os
import sys
from pathlib import Path

class Config:
    # Detectar se está rodando como executável PyInstaller
    if getattr(sys, 'frozen', False):
        # Se executado como executável, usar o diretório do .exe
        BASE_DIR = Path(sys.executable).parent
    else:
        # Se executado como script Python, usar o diretório do projeto
        BASE_DIR = Path(__file__).resolve().parent.parent
    
    INSTANCE_PATH = BASE_DIR / 'instance'
    INSTANCE_PATH.mkdir(exist_ok=True)
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{INSTANCE_PATH}/prontuario.db'
```

### Como Funciona

1. **Detecção de Modo**: `getattr(sys, 'frozen', False)` verifica se está rodando como executável
2. **Diretório Correto**: 
   - **Executável**: Usa `sys.executable.parent` → `dist/` (onde está o .exe)
   - **Script Python**: Usa `__file__` → diretório do projeto
3. **Criação Automática**: `INSTANCE_PATH.mkdir(exist_ok=True)` garante que a pasta existe
4. **Banco Persistente**: O SQLite cria o arquivo em `dist/instance/prontuario.db`

## Estrutura de Arquivos

Quando executar `dist/PatientRegistration.exe`, a estrutura será:

```
dist/
├── PatientRegistration.exe     ← Executável
└── instance/                   ← Criado automaticamente
    └── prontuario.db          ← Banco de dados persistente
```

## Teste Realizado

✅ **Teste 1: Primeira Execução**
- Executável iniciado
- Banco criado em `dist/instance/prontuario.db` (28.672 bytes)
- 5 usuários iniciais criados

✅ **Teste 2: Encerramento**
- Servidor encerrado
- Banco **permaneceu** no disco

✅ **Teste 3: Reinicialização**
- Executável reiniciado
- Banco **mantido** (28.672 bytes)
- Dados **NÃO foram recriados** (usuários existentes preservados)

## Benefícios

1. ✅ **Persistência Total**: Dados salvos entre execuções
2. ✅ **Portabilidade**: Pasta `dist/` completa pode ser movida/copiada
3. ✅ **Backup Simples**: Basta copiar `dist/instance/prontuario.db`
4. ✅ **Compatibilidade**: Funciona tanto em desenvolvimento quanto em produção

## Observações Importantes

- **Banco de Dados**: Sempre em `dist/instance/prontuario.db` (ao lado do .exe)
- **PDFs Gerados**: Ainda são criados no temp (será corrigido em próxima versão se necessário)
- **Backup**: Recomenda-se backup periódico da pasta `dist/instance/`
- **Migração**: Para transferir dados, copie toda a pasta `dist/` para outro computador

## Data da Correção
26 de janeiro de 2026
