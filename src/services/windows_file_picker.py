from __future__ import annotations

import base64
import os
import shutil
import subprocess
import threading
from pathlib import Path, PureWindowsPath


class FilePickerError(RuntimeError):
    pass


_picker_lock = threading.Lock()


_PICKER_SCRIPT = r"""
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Application]::EnableVisualStyles()
$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Title = 'Selecionar banco Access de pacientes'
$dialog.Filter = 'Banco Microsoft Access (*.accdb;*.mdb)|*.accdb;*.mdb'
$dialog.CheckFileExists = $true
$dialog.CheckPathExists = $true
$dialog.Multiselect = $false
if ($env:PATIENT_ACCESS_INITIAL_DIR -and (Test-Path -LiteralPath $env:PATIENT_ACCESS_INITIAL_DIR -PathType Container)) {
    $dialog.InitialDirectory = $env:PATIENT_ACCESS_INITIAL_DIR
}
if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    Write-Output $dialog.FileName
}
"""


def validate_local_access_path(value: str) -> str:
    text = (value or '').strip()
    path = PureWindowsPath(text)
    if not text or not path.is_absolute() or not path.drive or text.startswith(('\\\\', '//')):
        raise ValueError('Selecione um arquivo local com caminho absoluto neste computador.')
    if path.suffix.lower() not in {'.accdb', '.mdb'}:
        raise ValueError('Selecione um arquivo .accdb ou .mdb.')
    if not Path(text).is_file():
        raise ValueError('O arquivo selecionado não existe ou não está acessível.')
    return str(path)


def pick_local_access_database(initial_path: str | None = None, timeout: int = 180) -> str | None:
    if os.name != 'nt':
        raise FilePickerError('O seletor de arquivo local está disponível somente no Windows.')
    powershell = shutil.which('powershell.exe') or shutil.which('powershell')
    if not powershell:
        raise FilePickerError('O Windows PowerShell não foi encontrado neste computador.')

    initial_dir = ''
    if initial_path:
        candidate = Path(initial_path)
        initial_dir = str(candidate.parent if candidate.is_file() else candidate)

    encoded = base64.b64encode(_PICKER_SCRIPT.encode('utf-16le')).decode('ascii')
    environment = os.environ.copy()
    environment['PATIENT_ACCESS_INITIAL_DIR'] = initial_dir
    creation_flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    if not _picker_lock.acquire(blocking=False):
        raise FilePickerError('Já existe uma janela de seleção de arquivo aberta.')
    try:
        try:
            completed = subprocess.run(
                [powershell, '-NoProfile', '-STA', '-EncodedCommand', encoded],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=timeout,
                check=False,
                env=environment,
                creationflags=creation_flags,
            )
        except subprocess.TimeoutExpired as exc:
            raise FilePickerError('A seleção do arquivo excedeu o tempo limite.') from exc
        except OSError as exc:
            raise FilePickerError('O Windows não conseguiu iniciar a janela de seleção de arquivo.') from exc
    finally:
        _picker_lock.release()
    if completed.returncode != 0:
        raise FilePickerError('O Windows não conseguiu abrir a janela de seleção de arquivo.')

    selected = completed.stdout.strip()
    if not selected:
        return None
    try:
        return validate_local_access_path(selected)
    except ValueError as exc:
        raise FilePickerError(str(exc)) from exc
