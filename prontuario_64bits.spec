# -*- mode: python ; coding: utf-8 -*-
# Especificação do PyInstaller para build 64 bits

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/templates', 'src/templates'),
        ('src/static', 'src/static'),
        ('src/database', 'src/database'),
    ],
    hiddenimports=[
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'flask_wtf',
        'flask_migrate',
        'werkzeug',
        'sqlalchemy',
        'wtforms',
        'dotenv',
        'pypdf',
        'fillpdf',
        'alembic',
        'email_validator',
        'dateutil',
        'reportlab',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='prontuario-sistema-64bits',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='prontuario-64bits',
)
