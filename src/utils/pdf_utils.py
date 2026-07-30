"""Adaptadores legados de PDF, agora estritamente em memória.

As rotas ativas usam snapshots versionados. Estas funções permanecem apenas
para integrações internas antigas e nunca gravam bytes em disco.
"""
import logging
from pathlib import Path

from flask import current_app
from flask_login import current_user

from src.pdf.generator import generate_pdf
from src.pdf.mappings import build_hemocomponente_mapping, build_internacao_mapping


logger = logging.getLogger(__name__)


def _generate_pdf_bytes(document_type, values) -> bytes:
    try:
        pdf_bytes = generate_pdf(
            document_type, values, Path(current_app.root_path)
        )
        logger.info(
            'PDF finalizado em memória documento=%s bytes=%s',
            document_type, len(pdf_bytes),
        )
        return pdf_bytes
    except Exception:
        logger.exception('Falha na geração de PDF documento=%s', document_type)
        raise


def preencher_formulario_internacao(patient, surgery_data):
    values = build_internacao_mapping(patient, surgery_data, current_user)
    return _generate_pdf_bytes('internacao', values)


def preencher_requisicao_hemocomponente(patient, surgery_data):
    if not surgery_data.reserva_sangue:
        logger.info('PDF de hemocomponente não aplicável para esta solicitação.')
        return None
    values = build_hemocomponente_mapping(patient, surgery_data, current_user)
    return _generate_pdf_bytes('hemocomponente', values)


def preencher_formulario_internacao_direto(
    paciente, cirurgia, dados_medicos=None
):
    """Compatibilidade com chamadas legadas; retorna bytes finalizados."""
    values = build_internacao_mapping(paciente, cirurgia, current_user)
    if dados_medicos:
        values['SinaiseSintomas'] = dados_medicos.get('sintomas', '')
        values['JustificativaInternacao'] = dados_medicos.get(
            'condicoes_justificativas', ''
        )
        values['ResultadoExames'] = dados_medicos.get('resultados_exames', '')
        values['Peso'] = dados_medicos.get('peso', '')
    return _generate_pdf_bytes('internacao', values)


def get_pdf_fields(pdf_path):
    """Inspeciona os nomes dos widgets com a mesma biblioteca da geração."""
    import pymupdf

    document = pymupdf.open(pdf_path)
    try:
        return {
            widget.field_name: widget.field_value
            for page in document
            for widget in (page.widgets() or [])
        }
    finally:
        document.close()


def verificar_campos_pdf(pdf_path):
    return get_pdf_fields(pdf_path)