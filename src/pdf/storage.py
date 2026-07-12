import os
import tempfile
from pathlib import Path


def atomic_write_pdf(output_path: Path, pdf_bytes: bytes) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f'.{output_path.stem}-', suffix='.tmp', dir=str(output_path.parent)
    )
    try:
        with os.fdopen(fd, 'wb') as temporary:
            temporary.write(pdf_bytes)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, output_path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
    return output_path
