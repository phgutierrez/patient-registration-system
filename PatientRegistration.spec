# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['sqlalchemy.sql.default_comparator', 'waitress', 'flask', 'flask_sqlalchemy', 'flask_login', 'flask_wtf', 'flask_migrate', 'reportlab', 'reportlab.pdfgen', 'reportlab.lib', 'reportlab.platypus', 'PyPDF2', 'pyodbc', 'werkzeug', 'wtforms', 'email_validator', 'alembic', 'dateutil']
hiddenimports += collect_submodules('flask')
hiddenimports += collect_submodules('reportlab')
hiddenimports += collect_submodules('sqlalchemy')
hiddenimports += collect_submodules('wtforms')


a = Analysis(
    ['server.py'],
    pathex=[],
    binaries=[],
    datas=[('src', 'src'), ('migrations', 'migrations')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy.distutils', 'setuptools', 'pip', 'wheel', 'pytest', 'ipython', 'jupyter', 'notebook', 'sphinx', 'tkinter', 'test', 'unittest', 'doctest', 'pydoc', 'multiprocessing', 'distutils', 'lib2to3', 'pdb', 'dbm', 'curses', 'turtle'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PatientRegistration',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PatientRegistration',
)
