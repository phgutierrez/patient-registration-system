import os
from pathlib import Path
from fillpdf import fillpdfs
from flask import current_app
import traceback

def preencher_formulario_internacao(patient, surgery_data):
    """
    Preenche o formulário de internação com os dados do paciente e da cirurgia
    e retorna o caminho para o PDF gerado.
    """
    try:
        # Caminhos dos arquivos
        base_dir = Path(current_app.root_path)
        template_pdf = base_dir / 'static' / 'Internacao.pdf'
        
        # Verificar se o template existe
        if not os.path.exists(template_pdf):
            raise FileNotFoundError(f"Template de PDF não encontrado: {template_pdf}")
        
        # Criar diretório para PDFs preenchidos se não existir
        output_dir = base_dir / 'static' / 'preenchidos'
        os.makedirs(output_dir, exist_ok=True)
        
        # Nome do arquivo de saída
        output_filename = f"Internacao_{patient.id}_{patient.nome.replace(' ', '_')}.pdf"
        output_pdf = output_dir / output_filename
        
        # Calcular a data de internação e formatar hora da cirurgia
        data_cirurgia = surgery_data.data_cirurgia.strftime("%d/%m/%Y")
        hora_cirurgia = surgery_data.hora_cirurgia.strftime("%H:%M")
        
        data_internacao = data_cirurgia
        if surgery_data.internar_antes:
            from datetime import timedelta
            dia_anterior = surgery_data.data_cirurgia - timedelta(days=1)
            data_internacao = dia_anterior.strftime("%d/%m/%Y")
        
        # Obter os campos exatos do PDF para correspondência perfeita
        fields = fillpdfs.get_form_fields(str(template_pdf))
        print("Campos disponíveis no PDF:")
        for field_name, field_value in fields.items():
            print(f"  - {field_name}: {field_value}")
        
        # Preparar dados adaptados aos campos reais do PDF
        form_data = {}
        
        # Mapeamento dinâmico de campos - ajuste conforme os campos reais do seu PDF
        field_mapping = {
            'nome_paciente': ['Nome do Paciente', 'Nome_Paciente', 'nome', 'paciente'],
            'prontuario': ['Prontuário', 'prontuario', 'Prontuario'],
            'data_nascimento': ['Data de Nascimento', 'data_nascimento', 'nascimento'],
            'sexo': ['Sexo', 'sexo'],
            'cns': ['CNS', 'cns', 'Cartao_SUS'],
            'nome_mae': ['Nome da Mãe', 'Nome_Mae', 'mae'],
            'contato': ['Contato', 'contato', 'telefone'],
            'cidade': ['Cidade', 'cidade'],
            'diagnostico': ['Diagnóstico', 'diagnostico'],
            'cid': ['CID', 'cid'],
            'procedimento': ['Procedimento', 'procedimento'],
            'codigo_proc': ['Código Procedimento', 'codigo_procedimento', 'cod_procedimento'],
            'tipo_cirurgia': ['Tipo Cirurgia', 'tipo_cirurgia', 'tipo'],
            'data_cirurgia': ['Data Cirurgia', 'data_cirurgia'],
            'hora_cirurgia': ['Hora Cirurgia', 'hora_cirurgia'],
            'data_internacao': ['Data Internação', 'data_internacao'],
            'assistente': ['Assistente', 'assistente'],
            'reserva_sangue': ['Reserva Sangue', 'reserva_sangue'],
            'qtd_sangue': ['Quantidade Sangue', 'quantidade_sangue', 'qtd_sangue'],
            'raio_x': ['Raio X', 'raio_x'],
            'reserva_uti': ['Reserva UTI', 'reserva_uti'],
            'duracao': ['Duração Prevista', 'duracao_prevista', 'duracao'],
            'prescricao': ['Prescrição', 'prescricao'],
            'exames': ['Exames Pré-Op', 'exames_preop', 'exames']
        }
        
        # Valores a serem preenchidos
        values = {
            'nome_paciente': patient.nome,
            'prontuario': patient.prontuario,
            'data_nascimento': patient.data_nascimento.strftime("%d/%m/%Y"),
            'sexo': 'Masc' if patient.sexo == 'M' else 'Fem',
            'cns': patient.cns,
            'nome_mae': patient.nome_mae,
            'contato': patient.contato,
            'cidade': patient.cidade,
            'diagnostico': patient.diagnostico,
            'cid': patient.cid,
            'procedimento': surgery_data.procedimento_solicitado,
            'codigo_proc': surgery_data.codigo_procedimento,
            'tipo_cirurgia': surgery_data.tipo_cirurgia,
            'data_cirurgia': data_cirurgia,
            'hora_cirurgia': hora_cirurgia,
            'data_internacao': data_internacao,
            'assistente': surgery_data.assistente,
            'reserva_sangue': 'Sim' if surgery_data.reserva_sangue else 'Não',
            'qtd_sangue': surgery_data.quantidade_sangue or 'N/A',
            'raio_x': 'Sim' if surgery_data.raio_x else 'Não',
            'reserva_uti': 'Sim' if surgery_data.reserva_uti else 'Não',
            'duracao': surgery_data.duracao_prevista,
            'prescricao': surgery_data.prescricao_internacao or 'N/A',
            'exames': surgery_data.exames_preop or 'N/A'
        }
        
        # Para cada campo no PDF, tente encontrar o valor correspondente
        for field_name in fields.keys():
            found = False
            # Procurar correspondência no mapeamento
            for key, possible_names in field_mapping.items():
                if any(name.lower() in field_name.lower() for name in possible_names):
                    form_data[field_name] = values[key]
                    found = True
                    break
            
            # Se não encontrou correspondência, deixe o campo em branco
            if not found:
                print(f"Campo não mapeado: {field_name}")
                form_data[field_name] = ""
        
        print(f"Dados para preenchimento do PDF:")
        for k, v in form_data.items():
            print(f"  - {k}: {v}")
        
        # Preencher o PDF
        fillpdfs.write_fillable_pdf(str(template_pdf), str(output_pdf), form_data)
        
        print(f"PDF gerado com sucesso: {output_pdf}")
        
        return str(output_pdf)
    
    except Exception as e:
        print(f"Erro ao preencher formulário: {str(e)}")
        print(traceback.format_exc())
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