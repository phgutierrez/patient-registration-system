import os
from pathlib import Path
try:
    from fillpdf import fillpdfs
    FILLPDF_AVAILABLE = True
except ImportError:
    FILLPDF_AVAILABLE = False
    fillpdfs = None

from flask import current_app
from flask_login import current_user
import traceback
import logging
from datetime import datetime
from PyPDF2 import PdfWriter, PdfReader
from io import BytesIO

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
    """Obtém todos os campos do PDF - tenta fillpdfs primeiro, depois PyPDF2"""
    fields = {}
    try:
        # Tentar com fillpdfs primeiro
        if FILLPDF_AVAILABLE and fillpdfs:
            try:
                fillpdfs_fields = fillpdfs.get_form_fields(str(pdf_path))
                if fillpdfs_fields:
                    logger.info("Campos encontrados com fillpdfs:")
                    for field, value in fillpdfs_fields.items():
                        fields[field] = value
                        logger.info(f"  - {field}: {value}")

                if not fields:
                    logger.warning("Nenhum campo encontrado no PDF usando fillpdfs!")
                else:
                    logger.info(f"\nTotal de campos encontrados com fillpdfs: {len(fields)}")
                    return fields
            except Exception as e:
                logger.warning(f"fillpdfs falhou, tentando PyPDF2: {str(e)}")
        
        # Tentar com PyPDF2
        logger.info("Tentando ler campos com PyPDF2...")
        reader = PdfReader(str(pdf_path))
        
        # Verificar se o PDF tem fields
        if reader.get_fields():
            fields = reader.get_fields()
            logger.info(f"Campos encontrados com PyPDF2: {len(fields)}")
            for field_name in fields:
                logger.info(f"  - {field_name}")
            return fields
        else:
            logger.warning("Nenhum campo encontrado no PDF com PyPDF2")
            return {}
            
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
        logger.info("=" * 80)
        logger.info("INICIANDO GERAÇÃO DO PDF DE INTERNAÇÃO")
        logger.info("=" * 80)
        logger.info(f"Paciente: {patient.nome}")
        logger.info(f"ID do Paciente: {patient.id}")
        logger.info(f"Cirurgia ID: {surgery_data.id}")

        # Caminhos dos arquivos
        base_dir = Path(current_app.root_path)
        template_pdf = base_dir / 'static' / 'Internacao.pdf'
        logger.info(f"Caminho do template PDF: {template_pdf}")
        logger.info(f"Arquivo existe: {os.path.exists(template_pdf)}")

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

        # Obter os campos do PDF
        logger.info("\nOBTENDO CAMPOS DO PDF...")
        fields = get_pdf_fields(str(template_pdf))
        logger.info(f"Total de campos encontrados: {len(fields)}")
        
        if len(fields) == 0:
            logger.error("NENHUM CAMPO ENCONTRADO NO PDF!")
            logger.error("Isso indica que o PDF pode não ser preenchível ou usa um formato não suportado.")
            raise ValueError("Nenhum campo preenchível encontrado no PDF")
        
        logger.info("Campos encontrados no PDF:")
        for field in sorted(fields.keys()):
            logger.info(f"  - {field}")

        # Calcular a data de internação e formatar hora da cirurgia
        data_cirurgia = surgery_data.data_cirurgia.strftime("%d/%m/%Y")
        hora_cirurgia = surgery_data.hora_cirurgia.strftime("%H:%M")
        logger.info(f"\nData da cirurgia: {data_cirurgia}")
        logger.info(f"Hora da cirurgia: {hora_cirurgia}")

        data_internacao = data_cirurgia
        if surgery_data.internar_antes:
            from datetime import timedelta
            dia_anterior = surgery_data.data_cirurgia - timedelta(days=1)
            data_internacao = dia_anterior.strftime("%d/%m/%Y")
            logger.info(f"Internação um dia antes: {data_internacao}")

        # Preparar dados para preenchimento
        form_data = {}

        # Formatar telefone de contato (remover caracteres especiais)
        telefone_contato = ''.join(filter(str.isdigit, patient.contato)) if patient.contato else ''

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
            'CNS': patient.cns or '',
            'DNascimento': patient.data_nascimento.strftime("%d/%m/%Y"),
            'Sexo': 'Masc' if patient.sexo == 'M' else 'Fem',
            'SexoDescr': 'Masculino' if patient.sexo == 'M' else 'Feminino',
            'SexoDesc': 'Masculino' if patient.sexo == 'M' else 'Feminino',
            'Municipio': patient.cidade or '',
            'SinaiseSintomas': surgery_data.sinais_sintomas,
            'JustificativaInternacao': surgery_data.condicoes_justificativa,
            'ResultadoExames': surgery_data.resultados_diagnosticos,
            'Diagnostico Principal': patient.diagnostico or '',
            'DiagnosticoPrincipal': patient.diagnostico or '',
            'DiagnosticoPrincipal1': patient.diagnostico or '',
            'CID1': patient.cid or '',
            'CID2': surgery_data.cid_secundario if hasattr(surgery_data, 'cid_secundario') else '',
            'Procedimento': surgery_data.procedimento_solicitado,
            'Procedimento1': surgery_data.procedimento_solicitado,
            'Procedimento2': surgery_data.procedimento_solicitado,
            'Procedimento6': surgery_data.procedimento_solicitado,
            'Procedimento7': surgery_data.procedimento_solicitado,
            'Procedimento8': surgery_data.procedimento_solicitado,
            'CodigoSUS': surgery_data.codigo_procedimento,
            'DocMedico': current_user.cns or '',
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
            'Assistente': surgery_data.assistente or '',
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
            'CRM': current_user.crm or '',
            'OPME': surgery_data.opme or '',
            'OPME1': surgery_data.opme or '',
            'OPME2': surgery_data.opme or '',
            'OPME3': surgery_data.opme or '',
            'MaterialEspecial': surgery_data.opme or '',
            'MaterialEspecial1': surgery_data.opme or '',
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
        field_mapping['AparelhosEspeciais'] = combined_aparelhos_opme if combined_aparelhos_opme else 'Nenhum'

        logger.info("\nMapeamento de campos definido:")
        for key in sorted(field_mapping.keys()):
            logger.info(f"  - {key}")

        # Preencher apenas os campos que existem no PDF
        logger.info("\nPreenchendo formulário...")
        for pdf_field in fields.keys():
            # Tentar encontrar correspondência exata
            if pdf_field in field_mapping:
                form_data[pdf_field] = str(field_mapping[pdf_field])
                logger.info(f"  ✓ Campo '{pdf_field}' -> '{field_mapping[pdf_field]}'")
                continue

            # Tentar encontração case-insensitive
            found = False
            for key, value in field_mapping.items():
                if key.lower() == pdf_field.lower():
                    form_data[pdf_field] = str(value)
                    logger.info(f"  ✓ Campo '{pdf_field}' (case-insensitive match com '{key}') -> '{value}'")
                    found = True
                    break
            
            if not found:
                logger.warning(f"  ✗ Campo '{pdf_field}' não encontrado no mapeamento")
                form_data[pdf_field] = ""

        logger.info(f"\nTotal de campos preenchidos: {len(form_data)}")

        # Determinar número de páginas a incluir no PDF
        # Se OPME estiver vazio, incluir apenas as 5 primeiras páginas
        opme_value = (surgery_data.opme or "").strip()
        num_pages = None  # Por padrão, incluir todas as páginas
        
        if not opme_value:
            logger.info("OPME está vazio - gerando PDF com apenas 5 páginas (sem páginas 6-7)")
            num_pages = 5
        else:
            logger.info(f"OPME preenchido ({len(opme_value)} caracteres) - gerando PDF com todas as 7 páginas")

        # Preencher o PDF usando PyPDF2 (mais confiável que fillpdfs)
        logger.info("Iniciando preenchimento do PDF com PyPDF2...")
        preencer_pdf_com_pypdf2(str(template_pdf), str(output_pdf), form_data, num_pages=num_pages)

        logger.info(f"✓ PDF gerado com sucesso: {output_pdf}")
        file_size = os.path.getsize(output_pdf)
        logger.info(f"✓ Tamanho do arquivo: {file_size} bytes")
        logger.info("=" * 80)

        return str(output_pdf)

    except Exception as e:
        error_msg = f"Erro ao preencher formulário: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        raise e


def preencer_pdf_com_pypdf2(template_pdf, output_pdf, form_data, num_pages=None):
    """
    Preenche PDF usando PyPDF2 - método compatível com Adobe PDF Forms
    
    Args:
        template_pdf: Caminho do PDF template
        output_pdf: Caminho de saída do PDF preenchido
        form_data: Dicionário com dados para preenchimento
        num_pages: Número de páginas a incluir (None = todas as páginas)
    """
    try:
        logger.info("=" * 60)
        logger.info("PREENCHENDO PDF COM PyPDF2")
        logger.info("=" * 60)
        
        reader = PdfReader(template_pdf)
        writer = PdfWriter()
        
        # Obter campos do PDF
        pdf_fields = reader.get_fields()
        logger.info(f"Total de campos no PDF: {len(pdf_fields) if pdf_fields else 0}")
        logger.info(f"Total de páginas no template: {len(reader.pages)}")
        
        # Determinar quantas páginas copiar
        total_pages = len(reader.pages)
        pages_to_copy = num_pages if num_pages and num_pages < total_pages else total_pages
        
        logger.info(f"Copiando {pages_to_copy} página(s) do total de {total_pages}")
        
        # Copiar apenas as páginas especificadas
        for i in range(pages_to_copy):
            writer.add_page(reader.pages[i])
        
        # Converter todos os valores para string e preencher os campos
        form_data_str = {k: str(v) for k, v in form_data.items()}

        logger.info(f"Preenchendo {len(form_data_str)} campos em {len(writer.pages)} página(s)...")
        preenchidos = 0

        # Atualiza os campos em todas as páginas (há campos distribuídos em várias páginas)
        for page_index, page in enumerate(writer.pages):
            try:
                writer.update_page_form_field_values(page, form_data_str)
                preenchidos += 1
                logger.info(f"  ✓ Campos aplicados na página {page_index + 1}")
            except Exception as e:
                logger.warning(f"  ⚠ Não foi possível preencher a página {page_index + 1}: {str(e)}")

        logger.info(f"\nResumo: campos aplicados em {preenchidos} página(s)")
        
        # Salvar com os dados persistidos
        with open(output_pdf, 'wb') as out_file:
            writer.write(out_file)
        
        logger.info(f"✓ PDF salvo: {output_pdf}")
        logger.info(f"✓ Tamanho: {os.path.getsize(output_pdf)} bytes")
        logger.info(f"✓ Total de páginas no PDF gerado: {len(writer.pages)}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Erro ao preencher PDF: {str(e)}")
        logger.error(traceback.format_exc())
        raise
        raise

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


def preencher_formulario_internacao_direto(paciente, cirurgia, dados_medicos):
    """
    Preenche o formulário de internação com mapeamento direto usando fillpdfs.
    """
    try:
        # Caminhos dos arquivos
        template_path = os.path.join(
            current_app.root_path, 'static', 'Internacao.pdf')
        output_dir = os.path.join(
            current_app.root_path, 'static', 'preenchidos')
        os.makedirs(output_dir, exist_ok=True)

        # Nome do arquivo de saída
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Corrigido para usar ID da cirurgia se disponível, senão timestamp
        cirurgia_id_str = str(cirurgia.id) if hasattr(
            cirurgia, 'id') and cirurgia.id else timestamp
        output_filename = f"Internacao_{paciente.id}_{cirurgia_id_str}_{paciente.nome.replace(' ', '_')}.pdf"
        output_path = os.path.join(output_dir, output_filename)

        logger.info(
            "Iniciando preenchimento do formulário de internação (direto com fillpdfs)")
        logger.info(f"Template: {template_path}")
        # Corrected f-string to regular string
        logger.info("Output: {output_path}")

        # Mapeamento EXATO dos campos do PDF (baseado na inspeção)
        campos_exatos = {
            "NomePaciente": paciente.nome,
            "NomePaciente1": paciente.nome,
            "NomePaciente2": paciente.nome,
            "NomePaciente3": paciente.nome,
            "NomePaciente4": paciente.nome,
            "NomePaciente5": paciente.nome,
            "NomePaciente6": paciente.nome,
            "NomePaciente7": paciente.nome,
            "Nome do Paciente": paciente.nome,
            "Nome_Paciente": paciente.nome,
            "Nome": paciente.nome,
            "Paciente": paciente.nome,

            "Prontuario": str(paciente.prontuario),
            "Prontuario1": str(paciente.prontuario),
            "Prontuario2": str(paciente.prontuario),
            "Prontuario6": str(paciente.prontuario),
            "Prontuario7": str(paciente.prontuario),
            "Prontuário": str(paciente.prontuario),
            "Prontuario#1": str(paciente.prontuario),
            "Prontuario#2": str(paciente.prontuario),

            "NomeMae": paciente.nome_mae,
            "NomeMae1": paciente.nome_mae,
            "NomeMae2": paciente.nome_mae,
            "NomeMae5": paciente.nome_mae,
            "Nome da Mãe": paciente.nome_mae,
            "Nome_Mae": paciente.nome_mae,

            "TelContato": paciente.contato,
            "TelContato1": paciente.contato,
            "TelContato2": paciente.contato,
            "TelContato5": paciente.contato,
            "TelContato6": paciente.contato,

            "CNS": paciente.cns,
            "DNascimento": paciente.data_nascimento.strftime('%d/%m/%Y'),
            "Sexo": "Fem" if paciente.sexo == "F" else "Masc",
            "SexoDescr": "Feminino" if paciente.sexo == "F" else "Masculino",
            "SexoDesc": "Feminino" if paciente.sexo == "F" else "Masculino",
            "Municipio": paciente.cidade,

            "Idade": str(paciente.idade),
            "Idade1": str(paciente.idade),
            "Idade3": str(paciente.idade),
            "Idade4": str(paciente.idade),
            "Idade6": str(paciente.idade),

            # Endereço
            "Endereco1": paciente.endereco or "Não informado",
            "Endereco4": paciente.endereco or "Não informado",
            "Endereco5": paciente.endereco or "Não informado",
            "Endereco6": paciente.endereco or "Não informado",

            # Dados cirúrgicos
            "SinaiseSintomas": dados_medicos.get('sintomas', ''),
            "JustificativaInternacao": dados_medicos.get('condicoes_justificativas', ''),
            "ResultadoExames": dados_medicos.get('resultados_exames', ''),
            "Diagnostico Principal": cirurgia.condicoes_justificativa,
            "DiagnosticoPrincipal": cirurgia.condicoes_justificativa,
            "DiagnosticoPrincipal1": cirurgia.condicoes_justificativa,

            "CID1": cirurgia.codigo_procedimento[:4] if cirurgia.codigo_procedimento else '',
            "CID2": '',

            "Procedimento": cirurgia.procedimento_solicitado,
            "Procedimento1": cirurgia.procedimento_solicitado,
            "Procedimento2": cirurgia.procedimento_solicitado,
            "Procedimento6": cirurgia.procedimento_solicitado,
            "Procedimento7": cirurgia.procedimento_solicitado,
            "Procedimento8": cirurgia.procedimento_solicitado,

            "CodigoSUS": cirurgia.codigo_procedimento,

            "DocMedico": current_user.crm,
            "ProfissionalSolicitante": current_user.full_name,
            "ProfissionalSolicitante1": current_user.full_name,
            "ProfissionalSolicitante2": current_user.full_name,
            "ProfissionalSolicitante6": current_user.full_name,

            "DataCirurgia": cirurgia.data_cirurgia.strftime('%d/%m/%Y'),
            "HoraCirurgia": cirurgia.hora_cirurgia.strftime('%H:%M'),
            "Assistente": cirurgia.assistente,
            "Sangue": "Sim" if cirurgia.reserva_sangue else "Não",
            "QtdeSangue": str(cirurgia.quantidade_sangue) if cirurgia.reserva_sangue and cirurgia.quantidade_sangue else '',
            "RaioX": "Sim" if cirurgia.raio_x else "Não",
            "Duracao": cirurgia.duracao_prevista,

            "DataInternacao": cirurgia.data_cirurgia.strftime('%d/%m/%Y'),
            "DataInternacao1": cirurgia.data_cirurgia.strftime('%d/%m/%Y'),

            "Peso": str(dados_medicos.get('peso', '')),
            "Evolucao": cirurgia.evolucao_internacao or '',
            "Prescricao": cirurgia.prescricao_internacao or '',
            "ExamesPre": cirurgia.exames_preop or '',

            "DataSolicitacao": datetime.now().strftime('%d/%m/%Y'),
            "DataSolicitacao4": datetime.now().strftime('%d/%m/%Y'),
            "DataSolicitacao6": datetime.now().strftime('%d/%m/%Y'),
            "DataSolicitacao7": datetime.now().strftime('%d/%m/%Y'),
            "DataSolicitacao8": datetime.now().strftime('%d/%m/%Y'),

            "CRM": current_user.crm if hasattr(current_user, 'crm') else '',

            "AparelhosEspeciais": cirurgia.aparelhos_especiais + (" / OPME: " + cirurgia.opme if cirurgia.opme else ""),
            "OPME": cirurgia.opme or ''
        }

        logger.info("\nCampos exatos para preenchimento (fillpdfs):")
        for campo, valor in campos_exatos.items():
            logger.info(f"  - {campo} -> {valor}")

        # Preencher o PDF usando fillpdfs
        logger.info("Iniciando preenchimento do PDF com fillpdfs (direto)...")
        fillpdfs.write_fillable_pdf(
            template_path, output_path, campos_exatos, flatten=False)

        logger.info(f"PDF gerado com sucesso: {output_path}")
        return output_path

    except Exception as e:
        logger.error(
            f"Erro ao preencher formulário de internação (direto com fillpdfs): {str(e)}")
        logger.error(traceback.format_exc())
        raise


def preencher_requisicao_hemocomponente(patient, surgery_data):
    """
    Preenche o formulário de requisição de hemocomponente (sangue) com os dados
    do paciente e da cirurgia. Retorna o caminho para o PDF gerado ou None se
    reserva_sangue for False.
    """
    try:
        # Verificar se reserva de sangue foi solicitada
        if not surgery_data.reserva_sangue:
            logger.info("Reserva de sangue não solicitada. Pulando preenchimento de hemocomponente.")
            return None

        logger.info("=" * 80)
        logger.info("INICIANDO GERAÇÃO DO PDF DE REQUISIÇÃO DE HEMOCOMPONENTE")
        logger.info("=" * 80)
        logger.info(f"Paciente: {patient.nome}")
        logger.info(f"ID do Paciente: {patient.id}")
        logger.info(f"Cirurgia ID: {surgery_data.id}")

        # Caminhos dos arquivos
        base_dir = Path(current_app.root_path)
        template_pdf = base_dir / 'static' / 'REQUISIÇÃO HEMOCOMPONENTE.pdf'
        logger.info(f"Caminho do template PDF: {template_pdf}")
        logger.info(f"Arquivo existe: {os.path.exists(template_pdf)}")

        # Verificar se o template existe
        if not os.path.exists(template_pdf):
            error_msg = f"Template de PDF não encontrado: {template_pdf}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # Criar diretório para PDFs preenchidos se não existir
        output_dir = base_dir / 'static' / 'preenchidos'
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Diretório de saída: {output_dir}")

        # Nome do arquivo de saída
        output_filename = f"Hemocomponente_{patient.id}_{surgery_data.id}_{patient.nome.replace(' ', '_')}.pdf"
        output_pdf = output_dir / output_filename
        logger.info(f"Arquivo de saída: {output_pdf}")

        # Obter os campos do PDF
        logger.info("\nOBTENDO CAMPOS DO PDF...")
        fields = get_pdf_fields(str(template_pdf))
        logger.info(f"Total de campos encontrados: {len(fields)}")
        
        if len(fields) == 0:
            logger.error("NENHUM CAMPO ENCONTRADO NO PDF!")
            logger.error("Isso indica que o PDF pode não ser preenchível ou usa um formato não suportado.")
            raise ValueError("Nenhum campo preenchível encontrado no PDF")
        
        logger.info("Campos encontrados no PDF:")
        for field in sorted(fields.keys()):
            logger.info(f"  - {field}")

        # Calcular idade do paciente
        idade = patient.idade

        # Preparar dados para preenchimento
        form_data = {}

        # Mapeamento direto dos campos - focado nos campos principais do formulário de hemocomponente
        field_mapping = {
            # Campos de nome do paciente
            'Paciente': patient.nome,
            'NomePaciente': patient.nome,
            'Nome': patient.nome,
            'Nome Paciente': patient.nome,
            'Nome do Paciente': patient.nome,

            # Campos de idade
            'Idade': str(idade),
            'Idade_af_age': str(idade),

            # Campos de peso
            'Peso': str(surgery_data.peso) if surgery_data.peso else '',
            'Peso_af_number': str(surgery_data.peso) if surgery_data.peso else '',

            # Campo de data de nascimento
            'Data de Nascimento': patient.data_nascimento.strftime("%d/%m/%Y"),
            'Data de Nascimento_af_date': patient.data_nascimento.strftime("%d/%m/%Y"),
            'Data_Nascimento': patient.data_nascimento.strftime("%d/%m/%Y"),
            'DNascimento': patient.data_nascimento.strftime("%d/%m/%Y"),

            # Campos de diagnóstico e indicação clínica
            'Diagnóstico': patient.diagnostico or '',
            'Diagnostico': patient.diagnostico or '',
            'Diagnóstico e Indicação Clínica': patient.diagnostico or '',
            'Diagnostico e Indicacao Clinica': patient.diagnostico or '',
            'Indicação Clínica': patient.diagnostico or '',

            # Campo de cirurgia proposta / procedimento
            'Cirurgia Proposta': surgery_data.procedimento_solicitado,
            'Cirurgia_Proposta': surgery_data.procedimento_solicitado,
            'Procedimento': surgery_data.procedimento_solicitado,
            'Procedimento_af_text': surgery_data.procedimento_solicitado,

            # Campos adicionais que devem ser deixados em branco
            'CRM': '',
            'CRM_af_text': '',
            'CNS': '',
            'CNS_af_text': '',
            'Data da Solicitação': datetime.now().strftime("%d/%m/%Y"),
            'Data_Solicitacao': datetime.now().strftime("%d/%m/%Y"),
            'Hora da Solicitação': datetime.now().strftime("%H:%M"),
            'Observações': '',
            'Observacoes': '',
            'Notas': '',
        }

        logger.info("\nMapeamento de campos definido:")
        for key in sorted(field_mapping.keys()):
            logger.info(f"  - {key}")

        # Preencher apenas os campos que existem no PDF
        logger.info("\nPreenchendo formulário de hemocomponente...")
        for pdf_field in fields.keys():
            # Tentar encontrar correspondência exata
            if pdf_field in field_mapping:
                form_data[pdf_field] = str(field_mapping[pdf_field])
                logger.info(f"  ✓ Campo '{pdf_field}' -> '{field_mapping[pdf_field]}'")
                continue

            # Tentar encontração case-insensitive
            found = False
            for key, value in field_mapping.items():
                if key.lower() == pdf_field.lower():
                    form_data[pdf_field] = str(value)
                    logger.info(f"  ✓ Campo '{pdf_field}' (case-insensitive match com '{key}') -> '{value}'")
                    found = True
                    break
            
            if not found:
                logger.warning(f"  ✗ Campo '{pdf_field}' não encontrado no mapeamento; deixando em branco")
                form_data[pdf_field] = ""

        logger.info(f"\nTotal de campos preenchidos: {len(form_data)}")

        # Preencher o PDF usando PyPDF2
        logger.info("Iniciando preenchimento do PDF com PyPDF2...")
        preencer_pdf_com_pypdf2(str(template_pdf), str(output_pdf), form_data)

        logger.info(f"✓ PDF de hemocomponente gerado com sucesso: {output_pdf}")
        file_size = os.path.getsize(output_pdf)
        logger.info(f"✓ Tamanho do arquivo: {file_size} bytes")
        logger.info("=" * 80)

        return str(output_pdf)

    except Exception as e:
        error_msg = f"Erro ao preencher formulário de hemocomponente: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        raise e
