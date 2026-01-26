#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de validação para o Sistema de Registro de Pacientes
Verifica se todas as dependências estão instaladas e se o sistema está pronto para compilação
"""

import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Verifica versão do Python"""
    version = sys.version_info
    print(f"Python: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("  ⚠️  AVISO: Python 3.7+ recomendado (versão atual é inferior)")
        return False
    print("  ✓ OK")
    return True

def check_package(package_name, import_name=None):
    """Verifica se um pacote está instalado"""
    if import_name is None:
        import_name = package_name.replace('-', '_')
    
    try:
        __import__(import_name)
        print(f"  ✓ {package_name}")
        return True
    except ImportError:
        print(f"  ✗ {package_name} - NÃO INSTALADO")
        return False

def check_file_exists(file_path, description):
    """Verifica se um arquivo existe"""
    path = Path(file_path)
    if path.exists():
        size = path.stat().st_size
        print(f"  ✓ {description} ({size:,} bytes)")
        return True
    else:
        print(f"  ✗ {description} - NÃO ENCONTRADO")
        return False

def check_directory_exists(dir_path, description):
    """Verifica se um diretório existe"""
    path = Path(dir_path)
    if path.is_dir():
        files = len(list(path.glob('**/*')))
        print(f"  ✓ {description} ({files} arquivos/pastas)")
        return True
    else:
        print(f"  ✗ {description} - NÃO ENCONTRADO")
        return False

def main():
    print("\n" + "=" * 70)
    print("  VALIDAÇÃO - Sistema de Registro de Pacientes")
    print("=" * 70 + "\n")
    
    all_ok = True
    
    # Verificar Python
    print("1. Versão do Python:")
    if not check_python_version():
        all_ok = False
    
    # Verificar Dependências Essenciais
    print("\n2. Dependências Essenciais:")
    essential_packages = [
        ('Flask', 'flask'),
        ('Flask-SQLAlchemy', 'flask_sqlalchemy'),
        ('Flask-Login', 'flask_login'),
        ('SQLAlchemy', 'sqlalchemy'),
    ]
    
    for pkg, imp in essential_packages:
        if not check_package(pkg, imp):
            all_ok = False
    
    # Verificar Ferramentas de Compilação
    print("\n3. Ferramentas de Compilação:")
    build_packages = [
        ('PyInstaller', 'PyInstaller'),
        ('Waitress', 'waitress'),
    ]
    
    for pkg, imp in build_packages:
        if not check_package(pkg, imp):
            all_ok = False
    
    # Verificar Arquivos Importantes
    print("\n4. Arquivos do Projeto:")
    files_to_check = [
        ('wsgi.py', 'Arquivo WSGI'),
        ('run.py', 'Script principal'),
        ('requirements.txt', 'Arquivo de dependências'),
    ]
    
    for file, desc in files_to_check:
        if not check_file_exists(file, desc):
            all_ok = False
    
    # Verificar Diretórios Importantes
    print("\n5. Estrutura de Diretórios:")
    dirs_to_check = [
        ('src', 'Código-fonte'),
        ('src/templates', 'Templates HTML'),
        ('src/static', 'Arquivos estáticos'),
        ('src/models', 'Modelos'),
        ('src/routes', 'Rotas'),
    ]
    
    for dir_path, desc in dirs_to_check:
        if not check_directory_exists(dir_path, desc):
            all_ok = False
    
    # Verificar Scripts de Build
    print("\n6. Scripts de Build:")
    build_files = [
        ('prontuario_64bits.spec', 'Especificação 64 bits'),
        ('prontuario_32bits.spec', 'Especificação 32 bits'),
        ('build_releases.py', 'Script de compilação'),
    ]
    
    for file, desc in build_files:
        if not check_file_exists(file, desc):
            all_ok = False
    
    # Resumo
    print("\n" + "=" * 70)
    if all_ok:
        print("  ✓ SISTEMA VALIDADO COM SUCESSO!")
        print("\n  Você está pronto para compilar os releases.")
        print("  Execute: python build_releases.py")
        return 0
    else:
        print("  ✗ PROBLEMAS ENCONTRADOS!")
        print("\n  Instale as dependências faltantes:")
        print("    pip install -r requirements.txt")
        print("    pip install pyinstaller waitress")
        print("\n  Depois execute novamente este script.")
        return 1
    
    print("=" * 70 + "\n")

if __name__ == '__main__':
    sys.exit(main())
