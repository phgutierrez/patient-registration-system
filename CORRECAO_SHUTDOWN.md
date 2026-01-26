# Correção do Botão "Sair do Sistema"

## Problema Identificado
O botão "Sair do Sistema" apresentava erro ao tentar desligar o servidor no Windows devido à incompatibilidade entre o sinal `SIGTERM` e o servidor Waitress.

## Solução Implementada

### Alterações em `src/routes/main.py`

**Antes:**
```python
@main.route('/shutdown', methods=['POST'])
@login_required
def shutdown():
    try:
        os.kill(os.getpid(), signal.SIGTERM)
        return jsonify({'success': True, 'message': 'Servidor sendo encerrado...'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

**Depois:**
```python
@main.route('/shutdown', methods=['POST'])
@login_required
def shutdown():
    try:
        def shutdown_server():
            import time
            time.sleep(1)  # Aguardar a resposta ser enviada
            
            try:
                sys.exit(0)  # Método 1
            except:
                os._exit(0)  # Método 2 (fallback)
        
        threading.Thread(target=shutdown_server, daemon=True).start()
        return jsonify({'success': True, 'message': 'Servidor sendo encerrado...'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

## Como Funciona

1. **Thread Separada**: O shutdown é executado em uma thread daemon separada
2. **Delay de 1 segundo**: Aguarda a resposta HTTP ser enviada ao navegador antes de encerrar
3. **Duplo Fallback**: 
   - Primeiro tenta `sys.exit(0)` (encerramento gracioso)
   - Se falhar, usa `os._exit(0)` (encerramento forçado)
4. **Thread Daemon**: Garante que a thread não impeça o processo de finalizar

## Comportamento no Cliente

Quando o usuário clica no botão "Sair do Sistema":
1. ✅ Confirmação com diálogo
2. ✅ Requisição POST para `/shutdown`
3. ✅ Servidor responde com sucesso
4. ✅ Interface mostra mensagem "Sistema Encerrado com Sucesso"
5. ✅ Servidor encerra após 1 segundo
6. ✅ Tentativa automática de fechar a aba do navegador após 2 segundos

## Teste

Para testar a funcionalidade:
1. Execute `dist\PatientRegistration.exe`
2. Faça login no sistema
3. Clique no botão vermelho "Sair do Sistema" na barra lateral
4. Confirme o encerramento
5. Verifique se a mensagem de sucesso aparece
6. O processo deve ser finalizado automaticamente

## Data da Correção
26 de janeiro de 2026
