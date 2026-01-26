"""
Script para criar executáveis 32 e 64 bits com PyInstaller
Versão: 1.0.1 - Suporte multi-arquitetura
"""
import PyInstaller.__main__
import os
import shutil
import time
import sys
import platform

def remove_readonly(func, path, excinfo):
    """Callback para remover atributo readonly em Windows"""
    os.chmod(path, 0o777)
    func(path)

def clean_build_dirs():
    """Limpar builds anteriores"""
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder, onerror=remove_readonly)
                time.sleep(0.5)
            except Exception as e:
                print(f"Aviso: Não foi possível limpar pasta {folder}: {e}")

# Lista de módulos a excluir para reduzir tamanho
excludes = [
    'matplotlib',
    'numpy.distutils',
    'setuptools',
    'pip',
    'wheel',
    'pytest',
    'ipython',
    'jupyter',
    'notebook',
    'sphinx',
    'tkinter',
    'test',
    'unittest',
    'doctest',
    'pydoc',
    'multiprocessing',
    'distutils',
    'lib2to3',
    'pdb',
    'dbm',
    'curses',
    'turtle',
]

def get_pyinstaller_args(arch_suffix=''):
    """Retorna argumentos do PyInstaller"""
    exe_name = f'PatientRegistration{arch_suffix}'
    
    args = [
        'server.py',
        f'--name={exe_name}',
        '--onedir',
        '--noconsole',
        '--clean',
        '--noconfirm',
        '--add-data=src;src',
        '--add-data=migrations;migrations',
        '--hidden-import=sqlalchemy.sql.default_comparator',
        '--hidden-import=waitress',
        '--hidden-import=flask',
        '--hidden-import=flask_sqlalchemy',
        '--hidden-import=flask_login',
        '--hidden-import=flask_wtf',
        '--hidden-import=flask_migrate',
        '--hidden-import=reportlab',
        '--hidden-import=reportlab.pdfgen',
        '--hidden-import=reportlab.lib',
        '--hidden-import=reportlab.platypus',
        '--hidden-import=PyPDF2',
        '--hidden-import=pyodbc',
        '--hidden-import=werkzeug',
        '--hidden-import=wtforms',
        '--hidden-import=email_validator',
        '--hidden-import=alembic',
        '--hidden-import=dateutil',
        '--collect-submodules=flask',
        '--collect-submodules=reportlab',
        '--collect-submodules=sqlalchemy',
        '--collect-submodules=wtforms',
        '--copy-metadata=flask',
        '--copy-metadata=flask-sqlalchemy',
        '--copy-metadata=flask-login',
        '--copy-metadata=wtforms',
    ]
    
    for module in excludes:
        args.append(f'--exclude-module={module}')
    
    return args

def build_executable(arch_bits):
    """Compila executável para arquitetura específica"""
    print(f"\n{'='*70}")
    print(f"  COMPILANDO VERSÃO {arch_bits} BITS")
    print(f"{'='*70}\n")
    
    # Detectar arquitetura atual
    current_arch = platform.architecture()[0]
    print(f"Arquitetura do Python atual: {current_arch}")
    
    # Definir sufixo
    arch_suffix = f'-{arch_bits}bit' if arch_bits else ''
    
    # Executar PyInstaller
    try:
        PyInstaller.__main__.run(get_pyinstaller_args(arch_suffix))
        
        exe_path = f'dist/PatientRegistration{arch_suffix}/PatientRegistration{arch_suffix}.exe'
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"\n✅ Build {arch_bits} bits concluído com sucesso!")
            print(f"   Tamanho do executável: {size:.2f} MB")
            print(f"   Local: {exe_path}")
            return True
        else:
            print(f"\n❌ ERRO: Executável {arch_bits} bits não foi criado!")
            return False
    except Exception as e:
        print(f"\n❌ ERRO ao compilar versão {arch_bits} bits: {e}")
        return False

def main():
    """Função principal"""
    print("\n" + "="*70)
    print("  COMPILADOR MULTI-ARQUITETURA")
    print("  Sistema de Solicitação de Cirurgia - v1.0.1")
    print("="*70)
    
    # Detectar Python atual
    python_bits = '64' if sys.maxsize > 2**32 else '32'
    print(f"\nPython atual: {python_bits} bits")
    
    # Limpar builds anteriores
    print("\n🧹 Limpando builds anteriores...")
    clean_build_dirs()
    
    # Compilar versão 64 bits
    success_64 = build_executable('64')
    
    # Nota sobre compilação 32 bits
    if python_bits == '64':
        print("\n" + "="*70)
        print("  ATENÇÃO: COMPILAÇÃO 32 BITS")
        print("="*70)
        print("\n⚠️  Para compilar a versão 32 bits, você precisa:")
        print("   1. Instalar Python 32 bits separadamente")
        print("   2. Criar um ambiente virtual 32 bits")
        print("   3. Executar este script no ambiente 32 bits")
        print("\nPor enquanto, apenas a versão 64 bits foi compilada.")
        print("Se você já tem Python 32 bits instalado, execute:")
        print('   py -3.11-32 -m venv .venv32')
        print('   .venv32\\Scripts\\activate')
        print('   pip install -r requirements.txt')
        print('   python build_exe_multiarch.py')
    else:
        # Python 32 bits - compilar apenas 32 bits
        success_32 = build_executable('32')
        
        if success_32:
            print("\n" + "="*70)
            print("  ✅ COMPILAÇÃO CONCLUÍDA")
            print("="*70)
        else:
            print("\n❌ Falha na compilação 32 bits")
            return 1
    
    if success_64:
        print("\n" + "="*70)
        print("  ✅ BUILD MULTI-ARQUITETURA CONCLUÍDO")
        print("="*70)
        return 0
    else:
        print("\n❌ Falha na compilação")
        return 1

if __name__ == '__main__':
    exit(main())
