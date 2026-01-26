#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para construir releases 32 bits e 64 bits usando PyInstaller com Waitress
Cria executáveis independentes para ambas as arquiteturas
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_header(title):
    """Imprime um cabeçalho formatado"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def check_requirements():
    """Verifica se PyInstaller e Waitress estão instalados"""
    print_header("Verificando Requisitos")
    
    try:
        import PyInstaller
        print("✓ PyInstaller instalado")
    except ImportError:
        print("✗ PyInstaller não encontrado!")
        print("  Execute: pip install pyinstaller")
        return False
    
    try:
        import waitress
        print("✓ Waitress instalado")
    except ImportError:
        print("✗ Waitress não encontrado!")
        print("  Execute: pip install waitress")
        return False
    
    return True

def modify_wsgi_for_build():
    """Modifica o wsgi.py para usar Waitress ao invés de debug"""
    wsgi_content = """from src.app import app
import os

if __name__ == '__main__':
    # Importar Waitress para o servidor de produção
    from waitress import serve
    
    # Configurar a aplicação para produção
    app.config['ENV'] = 'production'
    app.config['DEBUG'] = False
    
    # Iniciar servidor na porta 5000
    serve(app, host='127.0.0.1', port=5000, threads=4)
"""
    
    with open('wsgi.py', 'w', encoding='utf-8') as f:
        f.write(wsgi_content)
    print("✓ wsgi.py configurado para usar Waitress")

def create_launcher_script():
    """Cria um script launcher que executa o servidor com Waitress"""
    launcher_content = """@echo off
REM Script launcher para o Sistema de Registro de Pacientes

echo Iniciando o Sistema de Registro de Pacientes...
timeout /t 2 /nobreak > nul

REM Abrir o navegador na página de login
start http://localhost:5000/login

REM Iniciar o aplicativo
prontuario-sistema.exe

pause
"""
    
    with open('launcher.bat', 'w', encoding='utf-8') as f:
        f.write(launcher_content)
    print("✓ launcher.bat criado")

def build_release(spec_file, arch_name):
    """Constrói um release usando o arquivo .spec fornecido"""
    print_header(f"Compilando Build {arch_name}")
    
    if not os.path.exists(spec_file):
        print(f"✗ Arquivo {spec_file} não encontrado!")
        return False
    
    try:
        # Limpar diretórios de build anteriores se existirem
        build_dir = f'build_{arch_name.lower()}'
        if os.path.exists(build_dir):
            print(f"  Limpando diretório {build_dir}...")
            shutil.rmtree(build_dir)
        
        # Executar PyInstaller
        cmd = [
            sys.executable, 
            '-m', 
            'PyInstaller',
            '--distpath', f'dist/{arch_name}',
            '--workpath', build_dir,
            spec_file
        ]
        
        print(f"\n  Executando: {' '.join(cmd)}\n")
        result = subprocess.run(cmd, check=True)
        
        print(f"\n✓ Build {arch_name} compilado com sucesso!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Erro ao compilar build {arch_name}:")
        print(f"  {e}")
        return False
    except Exception as e:
        print(f"✗ Erro inesperado: {e}")
        return False

def create_release_info():
    """Cria um arquivo com informações sobre os releases"""
    info_content = """# Releases - Sistema de Registro de Pacientes

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
"""
    
    with open('RELEASES.md', 'w', encoding='utf-8') as f:
        f.write(info_content)
    print("✓ RELEASES.md criado com informações")

def main():
    """Função principal"""
    print("\n" + "=" * 70)
    print("  GERADOR DE RELEASES - Sistema de Registro de Pacientes")
    print("  Versão 1.0.0 | Builds 32 bits e 64 bits")
    print("=" * 70)
    
    # Verificar requisitos
    if not check_requirements():
        sys.exit(1)
    
    # Modificar wsgi.py
    modify_wsgi_for_build()
    
    # Criar estrutura de diretórios
    print_header("Preparando Estrutura de Diretórios")
    os.makedirs('dist/64bits', exist_ok=True)
    os.makedirs('dist/32bits', exist_ok=True)
    print("✓ Diretórios criados em dist/")
    
    # Compilar releases
    results = {}
    results['64bits'] = build_release('prontuario_64bits.spec', '64bits')
    results['32bits'] = build_release('prontuario_32bits.spec', '32bits')
    
    # Criar arquivo de informações
    create_release_info()
    
    # Resumo
    print_header("RESUMO DA COMPILAÇÃO")
    
    all_success = True
    for arch, success in results.items():
        status = "✓ SUCESSO" if success else "✗ FALHOU"
        print(f"{arch}: {status}")
        if not success:
            all_success = False
    
    print("\n" + "=" * 70)
    
    if all_success:
        print("\n✓ TODOS OS RELEASES COMPILADOS COM SUCESSO!")
        print("\nArquivos gerados:")
        print("  - dist/64bits/  → Versão 64 bits")
        print("  - dist/32bits/  → Versão 32 bits")
        print("\nObs: A pasta dist/64bits/prontuario-64bits/ contém a build 64 bits")
        print("     A pasta dist/32bits/prontuario-32bits/ contém a build 32 bits")
        print("\nPróximos passos:")
        print("  1. Copie os arquivos dist/64bits/prontuario-64bits/ para distribuição")
        print("  2. Copie os arquivos dist/32bits/prontuario-32bits/ para distribuição")
        print("  3. Comprima cada pasta em um .zip para facilitar download")
        return 0
    else:
        print("\n✗ ALGUNS RELEASES FALHARAM")
        print("\nVerifique os erros acima e tente novamente.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
