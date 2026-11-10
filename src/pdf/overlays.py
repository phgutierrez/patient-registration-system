"""Elementos desenhados sobre o PDF depois do preenchimento do AcroForm.

Os overlays recebem o documento já achatado (``bake``) e os valores do
snapshot. Eles nunca leem o banco: tudo o que desenham precisa estar no
payload persistido, para que a regeneração de um snapshot antigo produza o
mesmo resultado.
"""
from __future__ import annotations

from typing import Mapping

import pymupdf

UTI_BANNER_KEY = '__ReservaUTI'
UTI_BANNER_TEXT = 'RESERVAR VAGA DE UTI'
# Mesmo tamanho do título "AVISO DE CIRURGIA" do modelo (Arial Black 15,96 pt).
UTI_BANNER_FONT_SIZE = 15.96
UTI_BANNER_FILL = (0.78, 0.95, 0.78)  # verde-claro
UTI_BANNER_TEXT_COLOR = (0, 0, 0)
UTI_BANNER_HEIGHT = 34.0
UTI_BANNER_GAP = 14.0
_ANCHOR_TITLE = 'AVISO DE CIRURGIA'
_ANCHOR_LABEL = 'DATA DA INTERNA'


class PdfOverlayError(RuntimeError):
    pass


def uti_banner_requested(values: Mapping[str, object]) -> bool:
    return str(values.get(UTI_BANNER_KEY, '') or '').strip().upper() == 'SIM'


def _find_surgery_notice_page(document: pymupdf.Document) -> pymupdf.Page:
    for page in document:
        if page.search_for(_ANCHOR_TITLE) and page.search_for(_ANCHOR_LABEL):
            return page
    raise PdfOverlayError(
        'Página "AVISO DE CIRURGIA" não encontrada para a faixa de UTI.'
    )


def draw_uti_banner(document: pymupdf.Document, values: Mapping[str, object]) -> None:
    """Desenha a faixa "RESERVAR VAGA DE UTI" abaixo da data de internação."""
    if not uti_banner_requested(values):
        return
    page = _find_surgery_notice_page(document)
    label = page.search_for(_ANCHOR_LABEL)[0]
    # O campo DataInternacao1 fica à direita do rótulo e é ~4 pt mais alto/baixo.
    anchor_bottom = max(label.y1, label.y0 + 22)
    left = label.x0
    right = page.rect.width - label.x0
    top = anchor_bottom + UTI_BANNER_GAP
    rect = pymupdf.Rect(left, top, right, top + UTI_BANNER_HEIGHT)
    if rect.y1 > page.rect.height:
        raise PdfOverlayError('Sem espaço para a faixa de UTI na página.')

    shape = page.new_shape()
    shape.draw_rect(rect)
    shape.finish(color=UTI_BANNER_FILL, fill=UTI_BANNER_FILL, width=0)
    shape.commit()

    text_height = UTI_BANNER_FONT_SIZE * 1.2
    padding = (rect.height - text_height) / 2
    text_rect = pymupdf.Rect(rect.x0, rect.y0 + padding, rect.x1, rect.y1 + 2)
    remaining = page.insert_textbox(
        text_rect,
        UTI_BANNER_TEXT,
        fontname='hebo',
        fontsize=UTI_BANNER_FONT_SIZE,
        color=UTI_BANNER_TEXT_COLOR,
        align=pymupdf.TEXT_ALIGN_CENTER,
    )
    if remaining < 0:
        raise PdfOverlayError('O texto da faixa de UTI não coube no espaço.')
