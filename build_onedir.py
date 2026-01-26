"""
Script para criar executável em modo ONE-DIR (pasta)
Vantagens: Inicialização mais rápida, melhor para distribuição com instalador
"""
import PyInstaller.__main__
import os
import shutil
import time

def remove_readonly(func, path, excinfo):
    """Callback para remover atributo readonly em Windows"""
    os.chmod(path, 0o777)
    func(path)

# Limpar builds anteriores
if os.path.exists('build'):
    try:
        shutil.rmtree('build', onerror=remove_readonly)
        time.sleep(0.5)
    except Exception as e:
        print(f"Aviso: {e}")

if os.path.exists('dist'):
    try:
        shutil.rmtree('dist', onerror=remove_readonly)
        time.sleep(0.5)
    except Exception as e:
        print(f"Aviso: {e}")

# Lista de módulos a excluir
excludes = [
    'matplotlib', 'numpy.distutils', 'setuptools', 'pip', 'wheel', 'pytest',
    'ipython', 'jupyter', 'notebook', 'sphinx', 'tkinter', 'test', 'unittest',
    'doctest', 'pydoc', 'multiprocessing', 'concurrent',
    'asyncio', 'distutils', 'lib2to3', 'pdb', 'dbm', 'curses', 'turtle',
]

# Configurações do PyInstaller (modo ONE-DIR)
pyinstaller_args = [
    'server.py',
    '--name=PatientRegistration',
    '--onedir',                           # MODO PASTA (mais rápido)
    '--noconsole',
    '--clean',
    '--noconfirm',
    
    # Dados
    '--add-data=src;src',
    '--add-data=migrations;migrations',
    
    # Hidden imports
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
    
    # Coletar submodules
    '--collect-submodules=flask',
    '--collect-submodules=reportlab',
    '--collect-submodules=sqlalchemy',
    '--collect-submodules=wtforms',
    
    # Metadata
    '--copy-metadata=flask',
    '--copy-metadata=flask-sqlalchemy',
    '--copy-metadata=flask-login',
    '--copy-metadata=flask-wtf',
    '--copy-metadata=reportlab',
]

# Adicionar exclusões
for module in excludes:
    pyinstaller_args.append(f'--exclude-module={module}')

print("=" * 70)
print("Build ONE-DIR (pasta) - Inicialização rápida")
print("=" * 70)
print(f"Nome: PatientRegistration")
print(f"Modo: One-dir (pasta com executável)")
print(f"Servidor: Waitress (produção)")
print("=" * 70)

PyInstaller.__main__.run(pyinstaller_args)

print("\n" + "=" * 70)
print("Build concluído!")
print("=" * 70)
print(f"Aplicação criada em: dist\\PatientRegistration\\")
print(f"Execute: dist\\PatientRegistration\\PatientRegistration.exe")
print("\nVantagens do modo ONE-DIR:")
print("- Inicialização 3-5x mais rápida")
print("- Melhor para distribuição com instalador")
print("- Mais fácil de atualizar arquivos específicos")
print("=" * 70)
