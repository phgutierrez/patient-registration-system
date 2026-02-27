"""
Build 32-bit do executavel Windows (perfil desktop/local).

Objetivo:
- refletir o fluxo de setup_windows.bat + run_local.bat
- empacotar somente o necessario do sistema atual
- manter onedir para inicializacao previsivel
"""
import os
import struct
import sys
from pathlib import Path

import PyInstaller.__main__


PROJECT_ROOT = Path(__file__).resolve().parent
ENTRYPOINT = PROJECT_ROOT / "server.py"
DIST_DIR = PROJECT_ROOT / "dist" / "Sistema32bits"
APP_NAME = "PatientRegistration"


EXCLUDES = [
    "matplotlib",
    "numpy",
    "numpy.distutils",
    "pandas",
    "setuptools.tests",
    "pytest",
    "ipython",
    "jupyter",
    "notebook",
    "sphinx",
    "tkinter",
    "test",
    "unittest",
    "doctest",
    "pydoc",
    "lib2to3",
    "pdb",
    "dbm",
    "curses",
    "turtle",
]


HIDDEN_IMPORTS = [
    "sqlalchemy.sql.default_comparator",
    "waitress",
    "flask",
    "flask_sqlalchemy",
    "flask_login",
    "flask_wtf",
    "flask_migrate",
    "sqlalchemy",
    "alembic",
    "PyPDF2",
    "fillpdf",
    "pyodbc",
    "requests",
    "icalendar",
    "dateutil",
    "pytz",
    "werkzeug",
    "wtforms",
]


def assert_prereqs() -> None:
    if not ENTRYPOINT.exists():
        raise FileNotFoundError(f"Entrypoint nao encontrado: {ENTRYPOINT}")

    if struct.calcsize("P") * 8 != 32:
        raise RuntimeError(
            "Build 32-bit requer Python 32-bit ativo. "
            "Ative a .venv32 antes de executar este script."
        )

    required_paths = [
        PROJECT_ROOT / "src",
        PROJECT_ROOT / "migrations",
        PROJECT_ROOT / "alembic.ini",
        PROJECT_ROOT / ".env.example",
    ]
    missing = [str(p) for p in required_paths if not p.exists()]
    if missing:
        raise FileNotFoundError("Arquivos/pastas obrigatorios ausentes:\n- " + "\n- ".join(missing))


def build_args() -> list[str]:
    args = [
        str(ENTRYPOINT),
        f"--name={APP_NAME}",
        "--onedir",
        "--noconsole",
        "--clean",
        "--noconfirm",
        f"--distpath={DIST_DIR}",
        "--add-data=src;src",
        "--add-data=migrations;migrations",
        "--add-data=alembic.ini;.",
        "--add-data=.env.example;.",
        "--collect-submodules=flask",
        "--collect-submodules=sqlalchemy",
        "--collect-submodules=wtforms",
        "--copy-metadata=flask",
        "--copy-metadata=flask-sqlalchemy",
        "--copy-metadata=flask-login",
        "--copy-metadata=flask-wtf",
        "--copy-metadata=waitress",
    ]

    for mod in HIDDEN_IMPORTS:
        args.append(f"--hidden-import={mod}")
    for mod in EXCLUDES:
        args.append(f"--exclude-module={mod}")
    return args


def main() -> None:
    assert_prereqs()

    print("=" * 72)
    print("Build 32-bit do executavel (perfil desktop/local)")
    print("=" * 72)
    print(f"Python: {sys.version.split()[0]} ({struct.calcsize('P') * 8}-bit)")
    print(f"Entrypoint: {ENTRYPOINT.name}")
    print(f"Saida: {DIST_DIR / APP_NAME}")
    print("Servidor: Waitress (localhost, desktop mode por padrao no executavel)")
    print("=" * 72)

    PyInstaller.__main__.run(build_args())

    print("\n" + "=" * 72)
    print("[OK] Build concluido")
    print("=" * 72)
    print(f"Executavel: {DIST_DIR / APP_NAME / (APP_NAME + '.exe')}")
    print("Teste recomendado:")
    print(f"  .\\dist\\Sistema32bits\\{APP_NAME}\\{APP_NAME}.exe")
    print("Distribuicao:")
    print(f"  Compactar a pasta dist\\Sistema32bits\\{APP_NAME}")
    print("=" * 72)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("\n[ERRO] Falha no build:")
        print(f"  {exc}")
        sys.exit(1)
