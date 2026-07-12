from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, FrozenSet, Optional


@dataclass(frozen=True)
class PdfDocumentSpec:
    identifier: str
    template_name: str
    expected_template_pages: int
    populated_pages: FrozenSet[int]
    required_fields: FrozenSet[str]
    flow: str
    output_prefix: str
    page_selector: Optional[Callable[[Dict[str, str]], int]] = None

    def template_path(self, app_root: Path) -> Path:
        return app_root / 'static' / self.template_name

    def output_pages(self, values: Dict[str, str]) -> int:
        if self.page_selector:
            return self.page_selector(values)
        return self.expected_template_pages


DOCUMENTS = {
    'internacao': PdfDocumentSpec(
        identifier='internacao',
        template_name='Internacao.pdf',
        expected_template_pages=7,
        populated_pages=frozenset(range(7)),
        required_fields=frozenset({'NomePaciente1', 'DataCirurgia', 'Procedimento1'}),
        flow='solicitação e edição de cirurgia',
        output_prefix='Internacao',
        page_selector=lambda values: 7 if values.get('OPME', '').strip() else 5,
    ),
    'hemocomponente': PdfDocumentSpec(
        identifier='hemocomponente',
        template_name='REQUISIÇÃO HEMOCOMPONENTE.pdf',
        expected_template_pages=2,
        populated_pages=frozenset({0}),
        required_fields=frozenset({'Paciente', 'Idade', 'Cirurgia Proposta'}),
        flow='reserva de sangue da solicitação cirúrgica',
        output_prefix='Hemocomponente',
    ),
}


def get_document_spec(identifier: str) -> PdfDocumentSpec:
    try:
        return DOCUMENTS[identifier]
    except KeyError as exc:
        raise ValueError(f'Tipo de documento PDF desconhecido: {identifier}') from exc
