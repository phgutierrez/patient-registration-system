# Troubleshooting - Especialidades Não Aparecem na Página Inicial

**Sintoma**: Após rodar `setup_windows.bat`, ao abrir o sistema em http://localhost:5000, a tela de seleção de especialidades aparece vazia.

## Causas Possíveis

### 1. Migrações Não Foram Aplicadas
**Causa**: A tabela `specialties` não foi criada pelo Alembic.

**Solução**:
```batch
REM Ativar ambiente virtual
.venv\Scripts\activate.bat

REM Aplicar migrações manualmente
alembic upgrade head

REM Verificar resultado
verify_setup.bat
```

### 2. Setup Interrompido
**Causa**: O script `setup_windows.bat` foi interrompido antes de completar todas as etapas.

**Solução**:
```batch
REM Resetar completamente
del instance\prontuario.db

REM Rodar setup novamente
setup_windows.bat
```

### 3. Banco de Dados Corrompido
**Causa**: Arquivo do banco foi deletado manualmente ou durante atualização.

**Solução**:
```batch
REM 1. Deletar banco corrompido
del instance\prontuario.db

REM 2. Rodar setup novamente (completo)
setup_windows.bat

REM 3. Verificar resultado
verify_setup.bat
```

## Verificar Se Especialidades Existem

Execute o script de verificação:

```batch
verify_setup.bat
```

Este script vai mostrar:
- ✓ Se tabelas do banco existem
- ✓ Se especialidades foram criadas
- ✓ Quantos usuários existem
- ✓ Status geral do setup

## Se Ainda Não Funcionar

### Opção 1: Recriar Banco Completo (Recomendado)

```batch
REM 1. Parar servidor (se estiver rodando)
REM   Pressione Ctrl+C no terminal

REM 2. Deletar banco
del instance\prontuario.db

REM 3. Deletar ambiente virtual
rmdir /s /q .venv

REM 4. Rodar setup do zero
setup_windows.bat
```

### Opção 2: Criar Especialidades Manualmente

```batch
REM 1. Ativar ambiente virtual
.venv\Scripts\activate.bat

REM 2. Criar especialidades via Python
python << PYTHON_SCRIPT
from src.app import create_app
from src.extensions import db
from src.models.specialty import Specialty

app = create_app()

with app.app_context():
    # Verificar se ja existem
    count = Specialty.query.count()
    
    if count == 0:
        specs = [
            Specialty(slug='ortopedia', name='Ortopedia', is_active=True),
            Specialty(slug='cirurgia_pediatrica', name='Cirurgia Pediatrica', is_active=True),
        ]
        for spec in specs:
            db.session.add(spec)
            print(f"Criada: {spec.name}")
        
        db.session.commit()
        print("\nEspecialidades criadas com sucesso!")
    else:
        print(f"Especialidades ja existem ({count})")
        for spec in Specialty.query.all():
            print(f"  - {spec.name}")

PYTHON_SCRIPT
```

### Opção 3: Verificar Arquivo .env

Se especialidades existem mas não aparecem, pode ser problema de configuração.

Verifique o arquivo `.env`:

```batch
REM Abrir arquivo
notepad .env
```

Deve ter pelo menos:
```
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=sua-chave-secreta-aqui
```

## Depois de Resolver

Sempre execute para confirmar:

```batch
verify_setup.bat
```

Se mostrar:
```
[OK] SETUP COMPLETADO COM SUCESSO!
```

Então pode executar:
```batch
run_local.bat
REM ou
run_network.bat
```

## Precisa de Mais Ajuda?

1. Abra GitHub Issues: https://github.com/phgutierrez/patient-registration-system/issues
2. Indique:
   - Output completo do `setup_windows.bat`
   - Output do `verify_setup.bat`
   - Versão do Python: `python --version`
   - Sistema operacional e versão
