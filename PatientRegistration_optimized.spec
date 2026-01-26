# -*- mode: python ; coding: utf-8 -*-
"""
Arquivo .spec otimizado para PyInstaller
Use: pyinstaller PatientRegistration_optimized.spec
"""

block_cipher = None

# Análise do executável
a = Analysis(
    ['server.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src', 'src'),
        ('migrations', 'migrations'),
    ],
    hiddenimports=[
        'sqlalchemy.sql.default_comparator',
        'waitress',
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'flask_wtf',
        'flask_migrate',
        'reportlab',
        'reportlab.pdfgen',
        'reportlab.lib',
        'reportlab.platypus',
        'PyPDF2',
        'pyodbc',
        'werkzeug',
        'wtforms',
        'email_validator',
        'alembic',
        'dateutil',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
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
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remover arquivos desnecessários para reduzir tamanho
a.datas = [x for x in a.datas if not x[0].startswith('tcl')]
a.datas = [x for x in a.datas if not x[0].startswith('tk')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PatientRegistration',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Ativar compressão UPX se disponível
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Mudar para True para ver erros no console
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
