# Releases - Sistema de Registro de Pacientes

## Versão: 1.0.0
Data de compilação: 26/01/2026

### Arquivos Disponíveis

#### 64 bits (64-bit)
- **Localização**: dist/64bits/
- **Executável**: prontuario-sistema-64bits.exe
- **Recomendado para**: Windows 64 bits (moderno, maioria dos computadores recentes)
- **Vantagens**: Melhor desempenho, mais memória disponível

#### 32 bits (32-bit)
- **Localização**: dist/32bits/
- **Executável**: prontuario-sistema-32bits.exe
- **Recomendado para**: Windows 32 bits (computadores antigos)
- **Compatibilidade**: Funciona em ambos 32 e 64 bits

### Como Usar

1. Baixe o arquivo apropriado para sua arquitetura
2. Execute o .exe
3. O servidor iniciará na porta 5000
4. O navegador abrirá automaticamente em http://localhost:5000/login
5. Faça login com suas credenciais

### Requisitos do Sistema

- Windows 7 ou superior
- Porta 5000 disponível
- Sem necessidade de Python instalado (tudo incluído no executável)

### Troubleshooting

Se a porta 5000 estiver em uso:
1. Feche outros aplicativos que usem a porta
2. Ou modifique o arquivo wsgi.py para usar uma porta diferente e recompile

### Notas Técnicas

- Servidor: Waitress
- Framework: Flask
- Banco de Dados: SQLite/PostgreSQL (conforme configuração)
- Arquitetura: Multi-threaded (4 threads)

### Suporte

Para questões técnicas ou problemas, verifique:
- Database.db deve estar na mesma pasta do executável
- Arquivo .env com configurações (se necessário)
