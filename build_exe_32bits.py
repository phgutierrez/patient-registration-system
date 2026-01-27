"""
Script otimizado para criar executável 32bits com PyInstaller
Reduz o tamanho do executável excluindo módulos desnecessários
Saída: dist/Sistema32bits/PatientRegistration

Nota: Este script cria um executável compilado para 32bits
Pode ser executado com Python 64bits, apenas criará o binário 32bits
"""
import PyInstaller.__main__
import os
import shutil
import time

def remove_readonly(func, path, excinfo):
    """Callback para remover atributo readonly em Windows"""
    os.chmod(path, 0o777)
    func(path)

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

# Configurações do PyInstaller para 32bits
pyinstaller_args = [
    'server.py',                          # Arquivo principal
    '--name=PatientRegistration',         # Nome do executável
    '--onedir',                           # Criar pasta com dependências (inicialização mais rápida)
    '--noconsole',                        # Não mostrar console (use --console para debug)
    '--clean',                            # Limpar cache antes de buildar
    '--noconfirm',                        # Não pedir confirmação para sobrescrever
    '--distpath=dist/Sistema32bits',      # Caminho de saída para 32bits
    '--target-arch=x86',                  # Compilar para 32bits (x86)
    
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
    '--hidden-import=pkg_resources',
    '--hidden-import=jaraco',
    '--hidden-import=jaraco.functools',
    '--hidden-import=jaraco.context',
    '--hidden-import=jaraco.text',
    
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
print("Iniciando build do executável 32BITS...")
print("=" * 70)
print(f"Arquitetura: 32 bits (x86)")
print(f"Nome: PatientRegistration.exe")
print(f"Modo: One-dir (pasta com dependências - inicialização rápida)")
print(f"Servidor: Waitress (produção)")
print(f"Saída: dist\\Sistema32bits\\PatientRegistration")
print(f"Otimizações: Ativadas")
print(f"Módulos excluídos: {len(excludes)}")
print("=" * 70)

# Executar PyInstaller
PyInstaller.__main__.run(pyinstaller_args)

print("\n" + "=" * 70)
print("Build 32bits concluído!")
print("=" * 70)
print(f"Executável criado em: dist\\Sistema32bits\\PatientRegistration\\PatientRegistration.exe")
print("\nBeneficios do modo --onedir:")
print("[OK] Inicializacao mais rapida")
print("[OK] Melhor desempenho em execucoes")
print("[OK] Facilita debugging e manutencao")
print("\nPara distribuir: Envie toda a pasta 'dist\\Sistema32bits\\PatientRegistration'")
print("=" * 70)
