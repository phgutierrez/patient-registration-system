import logging
import hashlib
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, FrozenSet, Iterable, Mapping, Optional, Set, Tuple

import pymupdf


logger = logging.getLogger(__name__)


class PdfGenerationError(RuntimeError):
    """Falha segura que impede a entrega de um PDF parcial."""


@dataclass(frozen=True)
class RenderResult:
    pdf_bytes: bytes
    resolved_fields: FrozenSet[str]
    template_pages: int
    output_pages: int
    verified_appearances: int


def _normalized_name(value: str) -> str:
    text = unicodedata.normalize('NFKD', value or '')
    text = ''.join(char for char in text if not unicodedata.combining(char))
    return re.sub(r'[^a-z0-9]+', '', text.casefold())


def resolve_mapping(field_name: str, values: Mapping[str, object]) -> Optional[Tuple[str, str]]:
    """Resolve nomes exatos, sem acento e nomes legados mal codificados do AcroForm."""
    if field_name in values:
        return field_name, str(values[field_name] or '')

    normalized = _normalized_name(field_name)
    candidates = [(key, value) for key, value in values.items() if _normalized_name(key) == normalized]
    if len(candidates) == 1:
        key, value = candidates[0]
        return key, str(value or '')

    # Um dos modelos contém nomes AcroForm com caracteres de acento corrompidos.
    # O fallback só é aceito quando há uma correspondência única e forte.
    ranked = sorted(
        ((SequenceMatcher(None, normalized, _normalized_name(key)).ratio(), key, value)
         for key, value in values.items()),
        reverse=True,
    )
    if ranked and ranked[0][0] >= 0.88:
        best_score, key, value = ranked[0]
        tied_values = {
            str(candidate_value or '')
            for score, _, candidate_value in ranked
            if score == best_score
        }
        if len(tied_values) == 1:
            return key, str(value or '')
    return None


def mapping_to_rect(mapping: Mapping[str, float]) -> pymupdf.Rect:
    return pymupdf.Rect(
        mapping['x'], mapping['y'],
        mapping['x'] + mapping['width'], mapping['y'] + mapping['height'],
    )


def convert_legacy_coordinates(page: pymupdf.Page, mapping: Mapping[str, float]) -> pymupdf.Rect:
    """Converte uma caixa com origem inferior para coordenadas superiores do PyMuPDF."""
    rect = mapping_to_rect(mapping)
    if mapping.get('origin', 'top') == 'bottom':
        height = page.cropbox.height
        rect = pymupdf.Rect(rect.x0, height - rect.y1, rect.x1, height - rect.y0)
    return rect * page.derotation_matrix


def insert_text_fitting_box(
    page: pymupdf.Page,
    rect: pymupdf.Rect,
    text: str,
    font_size: float,
    min_font_size: float,
    font_name: str = 'helv',
    align: int = pymupdf.TEXT_ALIGN_LEFT,
) -> float:
    size = font_size
    while size >= min_font_size:
        shape = page.new_shape()
        remaining = shape.insert_textbox(rect, text, fontsize=size, fontname=font_name, align=align)
        if remaining >= 0:
            shape.commit()
            return size
        size = round(size - 0.5, 2)
    raise PdfGenerationError('Um campo obrigatório não coube no espaço definido.')


def _set_widget_value(widget: pymupdf.Widget, value: str) -> None:
    if widget.field_type == pymupdf.PDF_WIDGET_TYPE_RADIOBUTTON:
        widget.field_value = value == widget.on_state()
    elif widget.field_type == pymupdf.PDF_WIDGET_TYPE_CHECKBOX:
        selected = value.casefold() in {'1', 'true', 'sim', 'yes', 'on', str(widget.on_state()).casefold()}
        widget.field_value = widget.on_state() if selected else False
    else:
        widget.field_value = value
    widget.update()


def render_acroform(
    template_path: Path,
    values: Mapping[str, object],
    *,
    expected_template_pages: int,
    output_pages: int,
    required_fields: Iterable[str],
) -> RenderResult:
    if not template_path.is_file():
        raise PdfGenerationError(f'Modelo PDF não encontrado: {template_path.name}')

    document = pymupdf.open(template_path)
    try:
        if document.page_count != expected_template_pages:
            raise PdfGenerationError(
                f'O modelo {template_path.name} possui {document.page_count} páginas; '
                f'eram esperadas {expected_template_pages}.'
            )
        if output_pages < 1 or output_pages > document.page_count:
            raise PdfGenerationError('Quantidade inválida de páginas solicitada.')
        if output_pages != document.page_count:
            document.select(range(output_pages))

        resolved: Set[str] = set()
        required = set(required_fields)
        required_appearances = {}
        widget_count = 0
        for page_number in range(document.page_count):
            page = document.load_page(page_number)
            widgets = list(page.widgets() or [])
            widget_count += len(widgets)
            for widget in widgets:
                match = resolve_mapping(widget.field_name or '', values)
                if match is None:
                    # O fluxo legado limpava explicitamente campos sem mapeamento,
                    # evitando que valores de exemplo do modelo vazassem na saída.
                    try:
                        _set_widget_value(widget, '')
                    except Exception as exc:
                        raise PdfGenerationError(
                            f'Não foi possível limpar o campo {widget.field_name!r} na página {page_number + 1}.'
                        ) from exc
                    continue
                mapping_name, value = match
                try:
                    if mapping_name in required and mapping_name not in required_appearances:
                        before = page.get_pixmap(clip=widget.rect, alpha=False)
                        required_appearances[mapping_name] = (
                            page_number,
                            pymupdf.Rect(widget.rect),
                            hashlib.sha256(before.samples).digest(),
                        )
                    _set_widget_value(widget, value)
                    resolved.add(mapping_name)
                    resolved.add(widget.field_name)
                except Exception as exc:
                    logger.exception(
                        'Falha ao preencher PDF modelo=%s pagina=%s campo=%s',
                        template_path.name, page_number + 1, widget.field_name,
                    )
                    raise PdfGenerationError(
                        f'Não foi possível preencher o campo {widget.field_name!r} na página {page_number + 1}.'
                    ) from exc

        if widget_count == 0:
            raise PdfGenerationError(f'O modelo {template_path.name} não possui campos AcroForm.')

        missing = [name for name in required if name not in resolved or not str(values.get(name, '')).strip()]
        if missing:
            raise PdfGenerationError('Campos obrigatórios do PDF não foram preenchidos: ' + ', '.join(sorted(missing)))

        document.bake(annots=True, widgets=True)
        unchanged = []
        for name, (page_number, rect, before_digest) in required_appearances.items():
            page = document.load_page(page_number)
            after = page.get_pixmap(clip=rect, alpha=False)
            if hashlib.sha256(after.samples).digest() == before_digest:
                unchanged.append(name)
        if unchanged:
            raise PdfGenerationError(
                'A aparência de campos obrigatórios não foi incorporada: ' + ', '.join(sorted(unchanged))
            )
        pdf_bytes = document.tobytes(garbage=4, deflate=True)
        return RenderResult(
            pdf_bytes, frozenset(resolved), expected_template_pages, output_pages,
            len(required_appearances),
        )
    finally:
        document.close()
