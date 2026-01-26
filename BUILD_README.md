# Build do Executável - Patient Registration System

## Requisitos
- Python 3.8+
- Dependências instaladas (requirements.txt)

## Como Criar o Executável

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Executar Build
```bash
python build_exe.py
```

O executável será gerado em: `dist\PatientRegistration.exe`

## Opções de Otimização

### Reduzir Tamanho com UPX
1. Baixe UPX: https://upx.github.io/
2. Extraia em uma pasta (ex: C:\upx)
3. Edite build_exe.py e adicione:
   ```python
   '--upx-dir=C:\\upx',
   ```

### Modo One-Dir (Mais Rápido)
Para inicialização mais rápida (mas gera uma pasta ao invés de um único arquivo):
- No build_exe.py, substitua `--onefile` por `--onedir`

### Incluir Console para Debug
Para ver mensagens de erro durante execução:
- No build_exe.py, remova a linha `'--windowed',`

## Estrutura do Executável

### Servidor
- Usa Waitress (servidor WSGI de produção)
- Padrão: http://127.0.0.1:5000
- 4 threads para requisições simultâneas

### Configuração
Variáveis de ambiente (opcionais):
- `HOST`: Endereço do servidor (padrão: 127.0.0.1)
- `PORT`: Porta do servidor (padrão: 5000)

## Tamanho Esperado
- Com otimizações: ~50-80 MB
- Sem otimizações: ~100-150 MB
- Com UPX: ~30-50 MB

## Troubleshooting

### Erro de Import
Se algum módulo não for encontrado, adicione em build_exe.py:
```python
'--hidden-import=nome_do_modulo',
```

### Arquivos Faltando
Para incluir arquivos adicionais:
```python
'--add-data=pasta_origem;pasta_destino',
```

### Teste Antes do Build
```bash
python server.py
```
