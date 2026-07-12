"""Gera artefatos sem dados reais para conferência manual em leitores de PDF."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pdf.generator import generate_pdf
from src.pdf.storage import atomic_write_pdf


OUTPUT = ROOT / 'test_artifacts' / 'pdf'


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    documents = {
        'internacao_sem_opme.pdf': ('internacao', {
            'NomePaciente1': 'PACIENTE ÁLVARO DE TESTE',
            'DataCirurgia': '20/07/2026',
            'Procedimento1': 'OSTEOTOMIA DE TESTE',
            'Sexo': 'Masc', 'Sangue': 'Nao', 'RaioX': 'Sim', 'OPME': '',
        }),
        'internacao_com_opme.pdf': ('internacao', {
            'NomePaciente1': 'PACIENTE CONCEIÇÃO DE TESTE',
            'DataCirurgia': '20/07/2026',
            'Procedimento1': 'OSTEOTOMIA DE TESTE',
            'Sexo': 'Fem', 'Sangue': 'Sim', 'RaioX': 'Nao', 'OPME': 'PLACA DE TESTE',
        }),
        'hemocomponente.pdf': ('hemocomponente', {
            'Paciente': 'PACIENTE JOÃO DE TESTE', 'Idade': '42',
            'Cirurgia Proposta': 'OSTEOTOMIA DE TESTE', 'Group4': 'Masculino',
            'Internação': 'SUS',
        }),
    }
    for filename, (document_type, values) in documents.items():
        path = OUTPUT / filename
        atomic_write_pdf(path, generate_pdf(document_type, values, ROOT / 'src'))
        print(path)


if __name__ == '__main__':
    main()
