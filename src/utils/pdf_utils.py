import os
from pathlib import Path
from fillpdf import fillpdfs
from flask import current_app
from flask_login import current_user
import traceback
import logging
from datetime import datetime
import PyPDF2

# Configurar o logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_generation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def get_pdf_fields(pdf_path):
    """Obtém todos os campos do PDF usando PyPDF2 e fillpdfs"""
    fields = {}
    try:
        # Primeiro tenta com fillpdfs
        fillpdfs_fields = fillpdfs.get_form_fields(str(pdf_path))
        if fillpdfs_fields:
            logger.info("Campos encontrados com fillpdfs:")
            for field, value in fillpdfs_fields.items():
                fields[field] = value
                logger.info(f"  - {field}: {value}")

        # Depois tenta com PyPDF2
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                if '/Annots' in page:
                    for annot in page['/Annots']:
                        obj = annot.get_object()
                        if '/T' in obj:
                            field_name = obj['/T']
                            # Converter de bytes para string se necessário
                            if isinstance(field_name, bytes):
                                field_name = field_name.decode('utf-8')
                            if field_name not in fields:
                                fields[field_name] = ''
                                logger.info(
                                    f"Campo adicional encontrado com PyPDF2: {field_name}")
                                logger.info(
                                    f"Tipo do campo: {obj.get('/FT', 'Desconhecido')}")
                                logger.info(
                                    f"Valor atual: {obj.get('/V', 'Vazio')}")
                                logger.info(f"Propriedades do campo: {obj}")

        if not fields:
            logger.warning("Nenhum campo encontrado no PDF!")
        else:
            logger.info(f"\nTotal de campos encontrados: {len(fields)}")
            logger.info("Lista completa de campos:")
            for field in fields:
                logger.info(f"  - {field}")

        return fields
    except Exception as e:
        logger.error(f"Erro ao ler campos do PDF: {str(e)}")
        logger.error(traceback.format_exc())
        return {}


def preencher_formulario_internacao(patient, surgery_data):
    """
    Preenche o formulário de internação com os dados do paciente e da cirurgia
    e retorna o caminho para o PDF gerado.
    """
    try:
        logger.info("Iniciando geração do PDF de internação")
        logger.info(f"Paciente: {patient.nome}")
        logger.info(f"ID do Paciente: {patient.id}")

        # Caminhos dos arquivos
        base_dir = Path(current_app.root_path)
        template_pdf = base_dir / 'static' / 'Internacao.pdf'
        logger.info(f"Caminho do template PDF: {template_pdf}")

        # Verificar se o template existe
        if not os.path.exists(template_pdf):
            error_msg = f"Template de PDF não encontrado: {template_pdf}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # Criar diretório para PDFs preenchidos se não existir
        output_dir = base_dir / 'static' / 'preenchidos'
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Diretório de saída: {output_dir}")

        # Nome do arquivo de saída - Incluindo ID da cirurgia
        output_filename = f"Internacao_{patient.id}_{surgery_data.id}_{patient.nome.replace(' ', '_')}.pdf"
        output_pdf = output_dir / output_filename
        logger.info(f"Arquivo de saída: {output_pdf}")

        # Calcular a data de internação e formatar hora da cirurgia
        data_cirurgia = surgery_data.data_cirurgia.strftime("%d/%m/%Y")
        hora_cirurgia = surgery_data.hora_cirurgia.strftime("%H:%M")
        logger.info(f"Data da cirurgia: {data_cirurgia}")
        logger.info(f"Hora da cirurgia: {hora_cirurgia}")

        data_internacao = data_cirurgia
        if surgery_data.internar_antes:
            from datetime import timedelta
            dia_anterior = surgery_data.data_cirurgia - timedelta(days=1)
            data_internacao = dia_anterior.strftime("%d/%m/%Y")
            logger.info(f"Internação um dia antes: {data_internacao}")

        # Obter os campos do PDF usando PyPDF2
        fields = get_pdf_fields(str(template_pdf))
        logger.info(f"\nTotal de campos encontrados: {len(fields)}")
        logger.info("Campos encontrados no PDF:")
        for field in fields:
            logger.info(f"  - {field}")

        # Preparar dados para preenchimento
        form_data = {}

        # Formatar telefone de contato (remover caracteres especiais)
        telefone_contato = ''.join(filter(str.isdigit, patient.contato))

        # Mapeamento direto dos campos
        field_mapping = {
            # Campos de nome do paciente (incluindo variações numeradas)
            'NomePaciente': patient.nome,
            'NomePaciente1': patient.nome,
            'NomePaciente2': patient.nome,
            'NomePaciente3': patient.nome,
            'NomePaciente4': patient.nome,
            'NomePaciente5': patient.nome,
            'NomePaciente6': patient.nome,
            'NomePaciente7': patient.nome,
            'Nome do Paciente': patient.nome,
            'Nome_Paciente': patient.nome,
            'Nome': patient.nome,
            'Paciente': patient.nome,

            # Campos de prontuário
            'Prontuario': patient.prontuario,
            'Prontuario1': patient.prontuario,
            'Prontuario2': patient.prontuario,
            'Prontuario6': patient.prontuario,
            'Prontuario7': patient.prontuario,
            'Prontuário': patient.prontuario,
            'Prontuario#1': patient.prontuario,
            'Prontuario#2': patient.prontuario,

            # Campos de nome da mãe
            'NomeMae': patient.nome_mae,
            'NomeMae1': patient.nome_mae,
            'NomeMae2': patient.nome_mae,
            'NomeMae5': patient.nome_mae,
            'Nome da Mãe': patient.nome_mae,
            'Nome_Mae': patient.nome_mae,

            # Campos de contato (formatados sem caracteres especiais)
            'TelContato': telefone_contato,
            'TelContato1': telefone_contato,
            'TelContato2': telefone_contato,
            'TelContato5': telefone_contato,
            'TelContato6': telefone_contato,

            # Outros campos
            'CNS': patient.cns,
            'DNascimento': patient.data_nascimento.strftime("%d/%m/%Y"),
            'Sexo': 'Masc' if patient.sexo == 'M' else 'Fem',
            'SexoDescr': 'Masculino' if patient.sexo == 'M' else 'Feminino',
            'SexoDesc': 'Masculino' if patient.sexo == 'M' else 'Feminino',
            'Municipio': patient.cidade,
            'SinaiseSintomas': surgery_data.sinais_sintomas,
            'JustificativaInternacao': surgery_data.condicoes_justificativa,
            'ResultadoExames': surgery_data.resultados_diagnosticos,
            'Diagnostico Principal': patient.diagnostico,
            'DiagnosticoPrincipal': patient.diagnostico,
            'DiagnosticoPrincipal1': patient.diagnostico,
            'CID1': patient.cid,
            'CID2': surgery_data.cid_secundario if hasattr(surgery_data, 'cid_secundario') else '',
            'Procedimento': surgery_data.procedimento_solicitado,
            'Procedimento1': surgery_data.procedimento_solicitado,
            'Procedimento2': surgery_data.procedimento_solicitado,
            'Procedimento6': surgery_data.procedimento_solicitado,
            'Procedimento7': surgery_data.procedimento_solicitado,
            'Procedimento8': surgery_data.procedimento_solicitado,
            'CodigoSUS': surgery_data.codigo_procedimento,
            'DocMedico': current_user.cns,  # Usando CNS do usuário logado
            # Nome completo do usuário logado
            'ProfissionalSolicitante': current_user.full_name,
            'ProfissionalSolicitante1': current_user.full_name,
            'ProfissionalSolicitante2': current_user.full_name,
            'ProfissionalSolicitante6': current_user.full_name,
            'Idade': str(patient.idade),
            'Idade1': str(patient.idade),
            'Idade3': str(patient.idade),
            'Idade4': str(patient.idade),
            'Idade6': str(patient.idade),
            'DataCirurgia': data_cirurgia,
            'HoraCirurgia': hora_cirurgia,
            'Assistente': surgery_data.assistente,
            # COMBINAR Aparelhos Especiais e OPME
            # 'AparelhosEspeciais': surgery_data.aparelhos_especiais or '',
            'Sangue': 'Sim' if surgery_data.reserva_sangue else 'Nao',
            'QtdeSangue': surgery_data.quantidade_sangue or '',
            'RaioX': 'Sim' if surgery_data.raio_x else 'Nao',
            'Duracao': surgery_data.duracao_prevista,
            'DataInternacao': data_internacao,
            'DataInternacao1': data_internacao,
            'Peso': str(surgery_data.peso),
            'Evolucao': surgery_data.evolucao_internacao or '',
            'Prescricao': surgery_data.prescricao_internacao or '',
            'ExamesPre': surgery_data.exames_preop or '',
            'DataSolicitacao': datetime.now().strftime("%d/%m/%Y"),
            'DataSolicitacao4': datetime.now().strftime("%d/%m/%Y"),
            'DataSolicitacao6': datetime.now().strftime("%d/%m/%Y"),
            'DataSolicitacao7': datetime.now().strftime("%d/%m/%Y"),
            'DataSolicitacao8': datetime.now().strftime("%d/%m/%Y"),
            'CRM': current_user.crm,  # CRM do usuário logado
            # 'OPME': surgery_data.opme or '',      # REMOVIDO - Será combinado
            # 'OPME1': surgery_data.opme or '',     # REMOVIDO - Será combinado
            'Endereco1': patient.endereco or '',
            'Endereco4': patient.endereco or '',
            'Endereco5': patient.endereco or '',
            'Endereco6': patient.endereco or ''
        }

        # Lógica para combinar Aparelhos Especiais e OPME
        aparelhos = surgery_data.aparelhos_especiais or ""
        opme_data = surgery_data.opme or ""
        combined_aparelhos_opme = aparelhos.strip()
        if combined_aparelhos_opme and opme_data.strip():
            combined_aparelhos_opme += " / OPME: " + opme_data.strip()
        elif opme_data.strip():
            combined_aparelhos_opme = "OPME: " + opme_data.strip()

        # Adicionar o campo combinado ao mapeamento
        # Garante que algo seja escrito
        field_mapping['AparelhosEspeciais'] = combined_aparelhos_opme if combined_aparelhos_opme else 'Nenhum'

        logger.info("\nMapeamento de campos:")
        for key, value in field_mapping.items():
            logger.info(f"  - {key} -> {value}")

        # Preencher os campos
        for pdf_field in fields:
            # Tentar encontrar correspondência exata
            if pdf_field in field_mapping:
                form_data[pdf_field] = field_mapping[pdf_field]
                logger.info(
                    f"Campo '{pdf_field}' mapeado diretamente com valor '{field_mapping[pdf_field]}'")
                continue

            # Tentar encontrar correspondência ignorando caracteres especiais e espaços
            base_field = ''.join(
                c for c in pdf_field if c.isalnum() or c.isspace()).strip()
            for key in field_mapping.keys():
                key_clean = ''.join(
                    c for c in key if c.isalnum() or c.isspace()).strip()
                if key_clean == base_field:
                    form_data[pdf_field] = field_mapping[key]
                    logger.info(
                        f"Campo '{pdf_field}' mapeado por limpeza com '{key}'")
                    break

            # Se ainda não encontrou, tentar correspondência ignorando maiúsculas/minúsculas
            if pdf_field not in form_data:
                for key, value in field_mapping.items():
                    if key.lower().replace(' ', '') == pdf_field.lower().replace(' ', ''):
                        form_data[pdf_field] = value
                        logger.info(
                            f"Campo '{pdf_field}' mapeado por similaridade com '{key}'")
                        break
                else:
                    logger.warning(f"Campo não mapeado: '{pdf_field}'")
                    form_data[pdf_field] = ""

        logger.info("\nDados finais para preenchimento:")
        for field, value in form_data.items():
            logger.info(f"  - {field}: {value}")

        # Preencher o PDF
        logger.info("Iniciando preenchimento do PDF...")
        fillpdfs.write_fillable_pdf(
            str(template_pdf), str(output_pdf), form_data)

        logger.info(f"PDF gerado com sucesso: {output_pdf}")

        return str(output_pdf)

    except Exception as e:
        error_msg = f"Erro ao preencher formulário: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        raise e


def verificar_campos_pdf(pdf_path):
    """
    Função utilitária para inspecionar os campos de um PDF preenchível.
    Útil para depuração.
    """
    try:
        print(f"Verificando campos do PDF: {pdf_path}")
        fields = fillpdfs.get_form_fields(str(pdf_path))
        print("Campos encontrados no PDF:")
        for field, value in fields.items():
            print(f"  - {field}: {value}")
        return fields
    except Exception as e:
        print(f"Erro ao verificar campos: {str(e)}")
        print(traceback.format_exc())
        return None
