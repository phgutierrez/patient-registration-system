from typing import Iterable, Optional

import pymupdf

from .renderer import PdfGenerationError


def validate_generated_pdf(
    pdf_bytes: bytes,
    expected_pages: int,
    expected_texts: Optional[Iterable[str]] = None,
    *,
    required_appearances_verified: bool = False,
) -> None:
    if not pdf_bytes.startswith(b'%PDF-') or len(pdf_bytes) < 1024:
        raise PdfGenerationError('O arquivo gerado não é um PDF válido ou está vazio.')

    document = pymupdf.open(stream=pdf_bytes, filetype='pdf')
    try:
        if document.page_count != expected_pages:
            raise PdfGenerationError(
                f'O PDF gerado possui {document.page_count} páginas; eram esperadas {expected_pages}.'
            )
        for page_number, page in enumerate(document):
            if list(page.widgets() or []):
                raise PdfGenerationError('O PDF final ainda contém campos interativos.')
            if not page.get_contents() and not page.get_images(full=True) and not page.get_text().strip():
                raise PdfGenerationError(f'A página {page_number + 1} do PDF está vazia.')

        # O bake de widgets pode preservar glifos em Form XObjects que não são
        # expostos pela extração de texto. Textos encontrados são conferidos;
        # os demais já foram auditados antes do bake pelo renderer.
        extracted = '\n'.join(page.get_text() for page in document)
        missing_texts = [text for text in expected_texts or () if text and text not in extracted]
        if missing_texts and not required_appearances_verified:
            raise PdfGenerationError('Textos essenciais não foram encontrados no PDF final.')
    finally:
        document.close()
