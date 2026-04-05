from __future__ import annotations

import os
import re
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path

from PyPDF2 import PdfReader, PdfWriter


def _normalize_text(value: str | None) -> str:
    if not value:
        return ''
    text = unicodedata.normalize('NFKD', str(value))
    return ''.join(ch for ch in text if not unicodedata.combining(ch)).strip().lower()


def _safe_filename(value: str) -> str:
    text = unicodedata.normalize('NFKD', value)
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r'[^a-zA-Z0-9_-]+', '_', text)
    return text.strip('_') or 'paciente'


def _get_pdf_fields(template_pdf: Path) -> dict:
    reader = PdfReader(str(template_pdf))
    return reader.get_fields() or {}


def _fill_pdf(template_pdf: Path, output_pdf: Path, field_values: dict[str, str], num_pages: int | None = None) -> None:
    reader = PdfReader(str(template_pdf))
    writer = PdfWriter()

    total_pages = len(reader.pages)
    pages_to_copy = num_pages if num_pages and num_pages < total_pages else total_pages

    for i in range(pages_to_copy):
        writer.add_page(reader.pages[i])

    string_values = {k: str(v) for k, v in field_values.items()}
    for page in writer.pages:
        writer.update_page_form_field_values(page, string_values)

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    with open(output_pdf, 'wb') as stream:
        writer.write(stream)


class PdfService:
    def __init__(self, static_dir: Path | None = None):
        self.static_dir = static_dir or Path('src/static')
        self.output_dir = self.static_dir / 'preenchidos'

    @staticmethod
    def _patient_age(patient) -> int:
        today = datetime.today().date()
        born = patient.data_nascimento
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    @staticmethod
    def _combine_aparelhos_opme(surgery) -> str:
        aparelhos = (surgery.aparelhos_especiais or '').strip()
        opme = (surgery.opme or '').strip()
        if _normalize_text(opme) == 'nao se aplica':
            opme = ''
        if aparelhos and opme:
            return f'{aparelhos} / OPME: {opme}'
        if opme:
            return f'OPME: {opme}'
        return aparelhos or 'Nenhum'

    async def generate_internacao_pdf(self, patient, surgery, user) -> str:
        template = self.static_dir / 'Internacao.pdf'
        if not template.exists():
            raise FileNotFoundError(f'Template não encontrado: {template}')

        age = self._patient_age(patient)
        telefone = ''.join(filter(str.isdigit, patient.contato or ''))
        data_cirurgia = surgery.data_cirurgia.strftime('%d/%m/%Y')
        hora_cirurgia = surgery.hora_cirurgia.strftime('%H:%M')
        data_internacao = data_cirurgia
        if surgery.internar_antes:
            data_internacao = (surgery.data_cirurgia - timedelta(days=1)).strftime('%d/%m/%Y')

        opme_raw = (surgery.opme or '').strip()
        opme_display = '' if _normalize_text(opme_raw) == 'nao se aplica' else opme_raw

        fields = _get_pdf_fields(template)
        if not fields:
            raise ValueError('Nenhum campo preenchível encontrado no PDF Internacao.pdf')

        mapping = {
            'NomePaciente': patient.nome,
            'NomePaciente1': patient.nome,
            'NomePaciente2': patient.nome,
            'NomePaciente3': patient.nome,
            'NomePaciente4': patient.nome,
            'NomePaciente5': patient.nome,
            'NomePaciente6': patient.nome,
            'NomePaciente7': patient.nome,
            'Prontuario': patient.prontuario,
            'Prontuario1': patient.prontuario,
            'Prontuario2': patient.prontuario,
            'Prontuario6': patient.prontuario,
            'Prontuario7': patient.prontuario,
            'NomeMae': patient.nome_mae,
            'NomeMae1': patient.nome_mae,
            'NomeMae2': patient.nome_mae,
            'TelContato': telefone,
            'TelContato1': telefone,
            'TelContato2': telefone,
            'CNS': patient.cns or '',
            'DNascimento': patient.data_nascimento.strftime('%d/%m/%Y'),
            'Sexo': 'Masc' if patient.sexo == 'M' else 'Fem',
            'SexoDescr': 'Masculino' if patient.sexo == 'M' else 'Feminino',
            'Municipio': patient.cidade or '',
            'SinaiseSintomas': surgery.sinais_sintomas,
            'JustificativaInternacao': surgery.condicoes_justificativa,
            'ResultadoExames': surgery.resultados_diagnosticos,
            'DiagnosticoPrincipal': patient.diagnostico or '',
            'CID1': patient.cid or '',
            'Procedimento': surgery.procedimento_solicitado,
            'Procedimento1': surgery.procedimento_solicitado,
            'Procedimento2': surgery.procedimento_solicitado,
            'Procedimento6': surgery.procedimento_solicitado,
            'Procedimento7': surgery.procedimento_solicitado,
            'CodigoSUS': surgery.codigo_procedimento,
            'DocMedico': user.cns or '',
            'ProfissionalSolicitante': user.full_name,
            'ProfissionalSolicitante1': user.full_name,
            'ProfissionalSolicitante2': user.full_name,
            'ProfissionalSolicitante6': user.full_name,
            'CRM': user.crm or '',
            'Idade': str(age),
            'Idade1': str(age),
            'Idade3': str(age),
            'Idade4': str(age),
            'Idade6': str(age),
            'DataCirurgia': data_cirurgia,
            'HoraCirurgia': hora_cirurgia,
            'Assistente': surgery.assistente or '',
            'Sangue': 'Sim' if surgery.reserva_sangue else 'Nao',
            'QtdeSangue': surgery.quantidade_sangue or '',
            'RaioX': 'Sim' if surgery.raio_x else 'Nao',
            'Duracao': surgery.duracao_prevista,
            'DataInternacao': data_internacao,
            'DataInternacao1': data_internacao,
            'Peso': str(surgery.peso),
            'Evolucao': surgery.evolucao_internacao or '',
            'Prescricao': surgery.prescricao_internacao or '',
            'ExamesPre': surgery.exames_preop or '',
            'DataSolicitacao': datetime.now().strftime('%d/%m/%Y'),
            'DataSolicitacao4': datetime.now().strftime('%d/%m/%Y'),
            'DataSolicitacao6': datetime.now().strftime('%d/%m/%Y'),
            'DataSolicitacao7': datetime.now().strftime('%d/%m/%Y'),
            'OPME': opme_display,
            'OPME1': opme_display,
            'OPME2': opme_display,
            'OPME3': opme_display,
            'MaterialEspecial': opme_display,
            'MaterialEspecial1': opme_display,
            'AparelhosEspeciais': self._combine_aparelhos_opme(surgery),
            'Endereco1': patient.endereco or '',
            'Endereco4': patient.endereco or '',
            'Endereco5': patient.endereco or '',
            'Endereco6': patient.endereco or '',
        }

        form_data = {}
        for field in fields.keys():
            if field in mapping:
                form_data[field] = mapping[field]
                continue
            lower = field.lower()
            for key, value in mapping.items():
                if key.lower() == lower:
                    form_data[field] = value
                    break
            else:
                form_data[field] = ''

        output_name = f"Internacao_{patient.id}_{surgery.id}_{_safe_filename(patient.nome)}.pdf"
        output_path = self.output_dir / output_name

        num_pages = 5 if not opme_display else None
        _fill_pdf(template, output_path, form_data, num_pages=num_pages)
        return output_name

    async def generate_hemocomponente_pdf(self, patient, surgery) -> str | None:
        if not surgery.reserva_sangue:
            return None

        template = self.static_dir / 'REQUISIÇÃO HEMOCOMPONENTE.pdf'
        if not template.exists():
            raise FileNotFoundError(f'Template não encontrado: {template}')

        age = self._patient_age(patient)
        fields = _get_pdf_fields(template)
        if not fields:
            raise ValueError('Nenhum campo preenchível encontrado no PDF de hemocomponente')

        mapping = {
            'Paciente': patient.nome,
            'NomePaciente': patient.nome,
            'Nome': patient.nome,
            'Idade': str(age),
            'Idade_af_age': str(age),
            'Peso': str(surgery.peso),
            'Peso_af_number': str(surgery.peso),
            'Data de Nascimento': patient.data_nascimento.strftime('%d/%m/%Y'),
            'Diagnóstico': patient.diagnostico or '',
            'Diagnostico': patient.diagnostico or '',
            'Diagnóstico e Indicação Clínica': patient.diagnostico or '',
            'Cirurgia Proposta': surgery.procedimento_solicitado,
            'Procedimento': surgery.procedimento_solicitado,
            'Data da Solicitação': datetime.now().strftime('%d/%m/%Y'),
            'Hora da Solicitação': datetime.now().strftime('%H:%M'),
            'Observações': '',
        }

        form_data = {}
        for field in fields.keys():
            if field in mapping:
                form_data[field] = mapping[field]
                continue
            lower = field.lower()
            for key, value in mapping.items():
                if key.lower() == lower:
                    form_data[field] = value
                    break
            else:
                form_data[field] = ''

        output_name = f"Hemocomponente_{patient.id}_{surgery.id}_{_safe_filename(patient.nome)}.pdf"
        output_path = self.output_dir / output_name
        _fill_pdf(template, output_path, form_data)
        return output_name

    async def remove_generated_file(self, filename: str | None) -> None:
        if not filename:
            return
        file_path = self.output_dir / filename
        if file_path.exists():
            os.remove(file_path)
