"""Adaptadores públicos de PDF preservados para compatibilidade com as rotas."""
import logging
from datetime import datetime
from pathlib import Path

from flask import current_app
from flask_login import current_user

from src.pdf.generator import generate_pdf
from src.pdf.mappings import build_hemocomponente_mapping, build_internacao_mapping
from src.pdf.storage import atomic_write_pdf


logger = logging.getLogger(__name__)


def _get_protected_output_dir() -> Path:
    output_dir = Path(current_app.config['PROTECTED_PDF_DIR'])
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _generate_to_protected_file(document_type, values, output_filename) -> str:
    try:
        pdf_bytes = generate_pdf(document_type, values, Path(current_app.root_path))
        output_path = _get_protected_output_dir() / output_filename
        atomic_write_pdf(output_path, pdf_bytes)
        logger.info(
            'PDF finalizado documento=%s arquivo=%s bytes=%s',
            document_type, output_filename, len(pdf_bytes),
        )
        return str(output_path)
    except Exception:
        logger.exception('Falha na geração de PDF documento=%s', document_type)
        raise


def preencher_formulario_internacao(patient, surgery_data):
    values = build_internacao_mapping(patient, surgery_data, current_user)
    filename = f"Internacao_{patient.id}_{surgery_data.id}_{patient.nome.replace(' ', '_')}.pdf"
    return _generate_to_protected_file('internacao', values, filename)


def preencher_requisicao_hemocomponente(patient, surgery_data):
    if not surgery_data.reserva_sangue:
        logger.info('PDF de hemocomponente não aplicável para esta solicitação.')
        return None
    values = build_hemocomponente_mapping(patient, surgery_data, current_user)
    filename = f"Hemocomponente_{patient.id}_{surgery_data.id}_{patient.nome.replace(' ', '_')}.pdf"
    return _generate_to_protected_file('hemocomponente', values, filename)


def preencher_formulario_internacao_direto(paciente, cirurgia, dados_medicos=None):
    """Compatibilidade com chamadas legadas; usa o mesmo renderer finalizado."""
    values = build_internacao_mapping(paciente, cirurgia, current_user)
    if dados_medicos:
        values['SinaiseSintomas'] = dados_medicos.get('sintomas', '')
        values['JustificativaInternacao'] = dados_medicos.get('condicoes_justificativas', '')
        values['ResultadoExames'] = dados_medicos.get('resultados_exames', '')
        values['Peso'] = dados_medicos.get('peso', '')
    surgery_identifier = getattr(cirurgia, 'id', None) or datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"Internacao_{paciente.id}_{surgery_identifier}_{paciente.nome.replace(' ', '_')}.pdf"
    return _generate_to_protected_file('internacao', values, filename)


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
