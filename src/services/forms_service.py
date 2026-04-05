from __future__ import annotations

import re
from datetime import datetime
from difflib import SequenceMatcher
from typing import Dict, List, Tuple

import requests

from src.core.config import Settings
from src.services.forms_mapping import get_forms_mapping


ORTHOPEDISTS = [
    'Dr. Laecio Damaceno',
    'Dr. Sávio Bruno',
    'Dr. Pedro Henrique',
    'Dr. Brauner Cavalcanti',
    'Dr. André Cristiano',
    'Dr. Bruno Montenegro',
    'Dr. Eduardo Lyra',
    'Dr. Jocemir',
    'Dr. Luiz Portela',
    'Dr. Francisco Neto',
    'Dr. Bartolomeu',
]


class FormsService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def get_forms_configuration(self) -> Tuple[str, str]:
        public_id = self.settings.google_forms_public_id or self.settings.default_google_forms_public_id
        view_url = self.settings.google_forms_viewform_url or f'https://docs.google.com/forms/d/e/{public_id}/viewform'
        if not public_id:
            raise ValueError('Google Forms PUBLIC_ID não configurado')
        return public_id, view_url

    @staticmethod
    def find_matching_orthopedist(user_full_name: str) -> str:
        normalized = user_full_name.strip().lower()
        for prefix in ['dr.', 'dr', 'dra.', 'dra', 'prof.', 'prof']:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):].strip()

        best_name = 'Não informado'
        best_ratio = 0.0
        for option in ORTHOPEDISTS:
            candidate = option.lower().replace('dr. ', '').strip()
            ratio = SequenceMatcher(None, normalized, candidate).ratio()
            if normalized and normalized.split()[0] in candidate:
                ratio = max(ratio, 0.7)
            if ratio > best_ratio:
                best_ratio = ratio
                best_name = option
        return best_name if best_ratio >= 0.5 else 'Não informado'

    @staticmethod
    def find_matching_opme(opme_text: str | None) -> Tuple[List[str], str]:
        options = [
            'Ilizarov Adulto',
            'Ilizarov Infantil',
            'Caixa 3,5mm',
            'Caixa 4,5mm',
            'Placa angulada',
            'Fios de Kirschner',
            'Parafuso Canulado',
            'Âncora',
            'Placa em 8',
            'Artrodese Coluna',
            'Não se aplica',
        ]
        if not opme_text or not opme_text.strip():
            return ['Não se aplica'], ''

        text = opme_text.strip()
        if text.lower() in {'nao se aplica', 'não se aplica'}:
            return ['Não se aplica'], ''

        selected: List[str] = []
        for option in options:
            if option.lower() in text.lower():
                selected.append(option)

        if selected:
            if 'Não se aplica' in selected:
                return ['Não se aplica'], ''
            return selected, ''

        other_match = re.search(r'Outro:\s*(.+)$', text, flags=re.IGNORECASE)
        if other_match:
            return [], other_match.group(1).strip()
        return [], text

    def build_forms_payload(self, surgery_request, patient, user_full_name: str) -> Dict[str, object]:
        if not surgery_request.procedimento_solicitado:
            raise ValueError('Procedimento solicitado é obrigatório')
        if not surgery_request.data_cirurgia:
            raise ValueError('Data da cirurgia é obrigatória')

        orthopedist = self.find_matching_orthopedist(user_full_name)
        opme, opme_other = self.find_matching_opme(surgery_request.opme)
        needs_icu = 'Sim' if surgery_request.reserva_uti else 'Não'

        lines = [
            f'Nome: {patient.nome}',
            f'Data de nascimento: {patient.data_nascimento.strftime("%d/%m/%Y")}',
            f'Diagnóstico: {patient.diagnostico}',
            f'Nº Prontuário: {patient.prontuario}',
            f'Contato: {patient.contato}',
        ]

        return {
            'orthopedist': orthopedist,
            'procedure_title': surgery_request.procedimento_solicitado,
            'date': surgery_request.data_cirurgia.strftime('%Y-%m-%d'),
            'full_description': '\n'.join(lines),
            'opme': opme,
            'opme_other': opme_other,
            'needs_icu': needs_icu,
        }

    def build_preview(self, payload: Dict[str, object]) -> Dict[str, object]:
        return {
            'title': payload['procedure_title'],
            'date_display': payload['date'],
            'orthopedist': payload['orthopedist'],
            'needs_icu_display': payload['needs_icu'],
            'opme_display': ', '.join(payload['opme']) if payload.get('opme') else 'Não',
            'description': payload['full_description'],
            'all_day': True,
        }

    def submit_form(self, payload: Dict[str, object], timeout: int | None = None) -> Tuple[bool, str, int]:
        public_id, _ = self.get_forms_configuration()
        mapping = get_forms_mapping()

        form_data: list[tuple[str, str]] = []
        form_data.append((mapping['ortopedista'], str(payload['orthopedist'])))
        form_data.append((mapping['procedimento'], str(payload['procedure_title'])))
        form_data.append((mapping['data'], str(payload['date'])))
        form_data.append((mapping['descricao'], str(payload['full_description'])))

        for item in payload.get('opme', []):
            form_data.append((mapping['opme'], str(item)))
        if payload.get('opme_other'):
            form_data.append((mapping['opme'], f"Outro: {payload['opme_other']}"))

        form_data.append((mapping['necessita_uti'], str(payload['needs_icu'])))

        submit_url = f'https://docs.google.com/forms/d/e/{public_id}/formResponse'

        try:
            response = requests.post(
                submit_url,
                data=form_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'Mozilla/5.0'},
                timeout=timeout or self.settings.google_forms_timeout,
                allow_redirects=True,
            )
        except requests.Timeout:
            return False, 'Timeout ao enviar para Google Forms', 504
        except requests.RequestException as exc:
            return False, f'Erro de conexão com Google Forms: {exc}', 502

        if response.status_code in (200, 302):
            return True, 'Resposta enviada ao Google Forms com sucesso', response.status_code
        if response.status_code == 403:
            return False, 'Formulário privado ou sem permissão de envio', 403
        if response.status_code == 404:
            return False, 'Formulário não encontrado (PUBLIC_ID inválido)', 404
        if response.status_code == 400:
            return False, 'Payload inválido para o Forms', 400
        return False, f'Google Forms retornou status {response.status_code}', response.status_code
