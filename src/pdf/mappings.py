import unicodedata
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Dict


def normalize_text(value: object) -> str:
    if not value:
        return ''
    text = unicodedata.normalize('NFKD', str(value))
    return ''.join(char for char in text if not unicodedata.combining(char)).strip().lower()


def _aliases(target: Dict[str, object], names, value: object) -> None:
    for name in names:
        target[name] = value if value is not None else ''


def _hemocomponent_weight_values(value: object) -> tuple[str, str]:
    """Retorna peso e Peso × 10 sem zeros decimais artificiais."""
    try:
        decimal_value = Decimal(str(value).strip().replace(',', '.'))
    except (InvalidOperation, ValueError, AttributeError):
        return '', ''
    if not decimal_value.is_finite() or decimal_value <= 0:
        return '', ''

    def clean(number: Decimal) -> str:
        text = format(number, 'f')
        return text.rstrip('0').rstrip('.') if '.' in text else text

    return clean(decimal_value), clean(decimal_value * Decimal('10'))


def build_internacao_mapping(patient, surgery, requester, now: datetime = None) -> Dict[str, object]:
    now = now or datetime.now()
    data_cirurgia = surgery.data_cirurgia.strftime('%d/%m/%Y')
    data_internacao = (
        (surgery.data_cirurgia - timedelta(days=1)).strftime('%d/%m/%Y')
        if surgery.internar_antes else data_cirurgia
    )
    telefone = ''.join(filter(str.isdigit, patient.contato or ''))
    opme_raw = (surgery.opme or '').strip()
    opme = '' if not opme_raw or normalize_text(opme_raw) == 'nao se aplica' else opme_raw
    aparelhos = (surgery.aparelhos_especiais or '').strip()
    combinado = aparelhos
    if combinado and opme:
        combinado += ' / OPME: ' + opme
    elif opme:
        combinado = 'OPME: ' + opme

    values: Dict[str, object] = {}
    _aliases(values, ['NomePaciente', 'NomePaciente1', 'NomePaciente2', 'NomePaciente3',
                      'NomePaciente4', 'NomePaciente5', 'NomePaciente6', 'NomePaciente7',
                      'Nome do Paciente', 'Nome_Paciente', 'Nome', 'Paciente'], patient.nome)
    _aliases(values, ['Prontuario', 'Prontuario1', 'Prontuario2', 'Prontuario6', 'Prontuario7',
                      'Prontuário', 'Prontuario#1', 'Prontuario#2'], patient.prontuario)
    _aliases(values, ['NomeMae', 'NomeMae1', 'NomeMae2', 'NomeMae5', 'Nome da Mãe', 'Nome_Mae'], patient.nome_mae)
    _aliases(values, ['TelContato', 'TelContato1', 'TelContato2', 'TelContato5', 'TelContato6'], telefone)
    _aliases(values, ['Idade', 'Idade1', 'Idade3', 'Idade4', 'Idade6'], patient.idade)
    _aliases(values, ['Endereco1', 'Endereco4', 'Endereco5', 'Endereco6'], patient.endereco or '')
    _aliases(values, ['Diagnostico Principal', 'DiagnosticoPrincipal', 'DiagnosticoPrincipal1'], patient.diagnostico or '')
    _aliases(values, ['Procedimento', 'Procedimento1', 'Procedimento2', 'Procedimento6',
                      'Procedimento7', 'Procedimento8'], surgery.procedimento_solicitado)
    _aliases(values, ['ProfissionalSolicitante', 'ProfissionalSolicitante1',
                      'ProfissionalSolicitante2', 'ProfissionalSolicitante6'], requester.full_name)
    _aliases(values, ['DataInternacao', 'DataInternacao1'], data_internacao)
    _aliases(values, ['DataSolicitacao', 'DataSolicitacao4', 'DataSolicitacao6',
                      'DataSolicitacao7', 'DataSolicitacao8'], now.strftime('%d/%m/%Y'))
    _aliases(values, ['OPME', 'OPME1', 'OPME2', 'OPME3', 'MaterialEspecial', 'MaterialEspecial1'], opme)
    values.update({
        'CNS': patient.cns or '',
        'DNascimento': patient.data_nascimento.strftime('%d/%m/%Y'),
        'Sexo': 'Masc' if patient.sexo == 'M' else 'Fem',
        'SexoDescr': 'Masculino' if patient.sexo == 'M' else 'Feminino',
        'SexoDesc': 'Masculino' if patient.sexo == 'M' else 'Feminino',
        'Municipio': patient.cidade or '',
        'SinaiseSintomas': surgery.sinais_sintomas or '',
        'JustificativaInternacao': surgery.condicoes_justificativa or '',
        'ResultadoExames': surgery.resultados_diagnosticos or '',
        'CID1': patient.cid or '',
        'CID2': getattr(surgery, 'cid_secundario', '') or '',
        'CodigoSUS': surgery.codigo_procedimento or '',
        'DocMedico': getattr(requester, 'cns', '') or '',
        'DataCirurgia': data_cirurgia,
        'HoraCirurgia': surgery.hora_cirurgia.strftime('%H:%M'),
        'Assistente': surgery.assistente or '',
        'AparelhosEspeciais': combinado or 'Nenhum',
        'Sangue': 'Sim' if surgery.reserva_sangue else 'Nao',
        'QtdeSangue': surgery.quantidade_sangue or '',
        'RaioX': 'Sim' if surgery.raio_x else 'Nao',
        'Duracao': surgery.duracao_prevista or '',
        'Peso': surgery.peso or '',
        'Evolucao': surgery.evolucao_internacao or '',
        'Prescricao': surgery.prescricao_internacao or '',
        'ExamesPre': surgery.exames_preop or '',
        'CRM': getattr(requester, 'crm', '') or '',
    })
    return values


def build_hemocomponente_mapping(patient, surgery, requester, now: datetime = None) -> Dict[str, object]:
    now = now or datetime.now()
    values: Dict[str, object] = {}
    weight, weight_times_ten = _hemocomponent_weight_values(getattr(surgery, 'peso', None))
    _aliases(values, ['Paciente', 'NomePaciente', 'Nome', 'Nome Paciente', 'Nome do Paciente'], patient.nome)
    _aliases(values, ['Idade', 'Idade_af_age'], patient.idade)
    _aliases(values, ['Peso', 'Peso_af_number'], weight)
    values['Texto5'] = weight_times_ten
    _aliases(values, ['Data de Nascimento', 'Data de Nascimento_af_date',
                      'Data_Nascimento', 'DNascimento'], patient.data_nascimento.strftime('%d/%m/%Y'))
    _aliases(values, ['Diagn\ufffdstico e Indica\ufffd\ufffdo Cl\ufffdnica',
                      'Diagnóstico', 'Diagnostico', 'Diagnóstico e Indicação Clínica',
                      'Diagnostico e Indicacao Clinica', 'Indicação Clínica'], 'Reserva para cirurgia')
    _aliases(values, ['Cirurgia Proposta', 'Cirurgia_Proposta', 'Procedimento',
                      'Procedimento_af_text'], surgery.procedimento_solicitado)
    _aliases(values, ['CRM', 'CRM_af_text'], getattr(requester, 'crm', '') or '')
    _aliases(values, ['CNS', 'CNS_af_text'], getattr(requester, 'cns', '') or '')
    _aliases(values, ['Data da Solicitação', 'Data_Solicitacao', 'DATA'], '')
    _aliases(values, ['Hora da Solicitação'], now.strftime('%H:%M'))
    _aliases(values, ['Observações', 'Observacoes', 'Notas'], '')
    values['Prontuário'] = patient.prontuario or ''
    values['Prontuario'] = patient.prontuario or ''
    values['Group4'] = 'Feminino' if patient.sexo == 'F' else 'Masculino'
    values['Internação'] = 'SUS'
    _aliases(values, [
        'PROGRAMADA Para determinada data e horaml de Concentrado de Hem\ufffdcias',
        'PROGRAMADA Para determinada data e horaml de Concentrado de Hemácias',
    ], 'X')
    return values
