"""
Script otimizado para criar executável com PyInstaller
Reduz o tamanho do executável excluindo módulos desnecessários
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
        time.sleep(0.5)  # Aguardar liberação de arquivos
    except Exception as e:
        print(f"Aviso: Não foi possível limpar pasta build: {e}")

if os.path.exists('dist'):
    try:
        shutil.rmtree('dist', onerror=remove_readonly)
        time.sleep(0.5)  # Aguardar liberação de arquivos
    except Exception as e:
        print(f"Aviso: Não foi possível limpar pasta dist: {e}")

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
    'xml.etree',
    'xml.dom',
    'xml.sax',
    'multiprocessing',
    'distutils',
    'lib2to3',
    'pdb',
    'dbm',
    'curses',
    'turtle',
]

# Configurações do PyInstaller
pyinstaller_args = [
    'server.py',                          # Arquivo principal
    '--name=PatientRegistration',         # Nome do executável
    '--onefile',                          # Criar um único arquivo executável
    '--noconsole',                        # Não mostrar console (use --console para debug)
    '--clean',                            # Limpar cache antes de buildar
    '--noconfirm',                        # Não pedir confirmação para sobrescrever
    
    # Adicionar dados necessários
    '--add-data=src;src',                 # Incluir pasta src
    '--add-data=migrations;migrations',   # Incluir migrations
    
    # Ícone (opcional - crie um arquivo icon.ico se quiser)
    # '--icon=icon.ico',
    
    # Hidden imports (módulos que PyInstaller pode não detectar)
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
    
    # Coletar dados de pacotes
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
print("Iniciando build do executável...")
print("=" * 70)
print(f"Nome: PatientRegistration.exe")
print(f"Modo: One-file (executável único)")
print(f"Servidor: Waitress (produção)")
print(f"Otimizações: Ativadas")
print(f"Módulos excluídos: {len(excludes)}")
print("=" * 70)

# Executar PyInstaller
PyInstaller.__main__.run(pyinstaller_args)

print("\n" + "=" * 70)
print("Build concluído!")
print("=" * 70)
print(f"Executável criado em: dist\\PatientRegistration.exe")
print("\nDicas para reduzir ainda mais o tamanho:")
print("1. Use UPX (compressor de executáveis): --upx-dir=<caminho_upx>")
print("2. Remova arquivos .pyc não utilizados")
print("3. Considere usar --onedir ao invés de --onefile para inicialização mais rápida")
print("=" * 70)
