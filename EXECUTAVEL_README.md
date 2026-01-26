# Patient Registration System - Guia de Build

## ✅ Status do Build
- **Executável gerado**: `dist\PatientRegistration.exe`
- **Tamanho**: ~40 MB (otimizado)
- **Servidor**: Waitress (produção)
- **Modo**: One-file (executável único)

## 🚀 Uso Rápido

### Executar o Executável
```bash
# Opção 1: Duplo clique
dist\PatientRegistration.exe

# Opção 2: Via batch
run_exe.bat

# Opção 3: Via PowerShell
.\dist\PatientRegistration.exe
```

O servidor iniciará em: http://127.0.0.1:5000

## 🔧 Reconstruir o Executável

### Método 1: Build Rápido (Recomendado)
```bash
python build_exe.py
```

### Método 2: Build com arquivo .spec
```bash
pyinstaller PatientRegistration_optimized.spec
```

### Método 3: Build ONE-DIR (mais rápido para executar)
```bash
python build_onedir.py
```

## 📦 Opções de Build

### ONE-FILE vs ONE-DIR

**ONE-FILE** (build_exe.py)
- ✅ Um único arquivo executável
- ✅ Fácil distribuição
- ⚠️ Inicialização mais lenta
- **Tamanho**: ~40 MB

**ONE-DIR** (build_onedir.py)
- ✅ Inicialização 3-5x mais rápida
- ✅ Melhor para instaladores
- ⚠️ Múltiplos arquivos em pasta
- **Tamanho**: ~50-60 MB (total da pasta)

## 🎯 Otimizações Aplicadas

### Redução de Tamanho
1. ✅ Exclusão de 29 módulos desnecessários
2. ✅ Remoção de bibliotecas de teste
3. ✅ Exclusão de documentação
4. ✅ Otimização de imports

### Performance
1. ✅ Waitress (4 threads)
2. ✅ Compressão UPX (se disponível)
3. ✅ Hidden imports otimizados

## 🔽 Reduzir Ainda Mais o Tamanho

### Usar UPX (Recomendado)
Pode reduzir para ~25-30 MB

1. Baixar UPX: https://github.com/upx/upx/releases
2. Extrair em `C:\upx`
3. Editar `build_exe.py` e adicionar:
   ```python
   '--upx-dir=C:\\upx',
   ```

### Remover Pandas (se não usado)
Se o pandas não for necessário:

1. Remover de `requirements.txt`
2. Adicionar em excludes do `build_exe.py`:
   ```python
   'pandas',
   'numpy',
   ```

Redução estimada: ~10-15 MB

## 📋 Estrutura de Arquivos

```
dist/
├── PatientRegistration.exe    # ONE-FILE
│
└── PatientRegistration/        # ONE-DIR
    ├── PatientRegistration.exe
    ├── _internal/
    └── ...
```

## 🐛 Troubleshooting

### Erro ao Iniciar
- Remover `--noconsole` do build_exe.py
- Reconstruir para ver erros

### Imports Faltando
Adicionar em `build_exe.py`:
```python
'--hidden-import=modulo_faltante',
```

### Arquivos/Templates Não Encontrados
Verificar se estão em `src/` e incluídos no build

## 🔐 Configuração de Produção

### Variáveis de Ambiente
Criar arquivo `.env` ao lado do .exe:
```env
HOST=0.0.0.0
PORT=5000
SECRET_KEY=sua_chave_secreta
DATABASE_URL=sua_url_banco
```

### Executar em Porta Diferente
```bash
set PORT=8080 && dist\PatientRegistration.exe
```

## 📊 Comparação de Tamanhos

| Método | Tamanho | Velocidade | Distribuição |
|--------|---------|------------|--------------|
| ONE-FILE | ~40 MB | Normal | ⭐⭐⭐⭐⭐ |
| ONE-DIR | ~50 MB | Rápida | ⭐⭐⭐ |
| ONE-FILE + UPX | ~25 MB | Normal | ⭐⭐⭐⭐⭐ |

## 🎁 Criar Instalador (Opcional)

### Usando Inno Setup
1. Baixar: https://jrsoftware.org/isinfo.php
2. Criar script de instalação
3. Incluir executável + dependências

### Usando NSIS
Alternativa ao Inno Setup para criar instaladores Windows

## 📝 Notas Importantes

1. **Banco de Dados**: Certifique-se de que o banco está acessível
2. **Migrations**: Executar antes de distribuir
3. **Arquivos Estáticos**: Incluídos automaticamente da pasta `src/`
4. **PDFs**: Pasta `src/static/pdfs/gerados/` deve existir

## 🔄 Atualização

Para atualizar o executável:
1. Fazer alterações no código
2. Executar `python build_exe.py`
3. Substituir o .exe antigo pelo novo
