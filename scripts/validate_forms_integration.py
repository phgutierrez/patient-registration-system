"""
Script de validação: Teste completo do fluxo de agendamento via Forms

Este script testa o fluxo completo sem precisar da interface web:
1. Valida configurações
2. Testa extração de entry IDs
3. Testa construção de payload
4. Testa submissão ao Forms (opcional)

USO:
    python scripts/validate_forms_integration.py

OPÇÕES:
    --skip-submit    Não tenta submeter ao Forms (apenas valida)
    --force-refresh  Força download do HTML do Forms
"""

import sys
import argparse
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app import create_app
from src.services.forms_service import (
    get_or_refresh_mapping,
    build_forms_payload,
    submit_form
)


class MockPatient:
    """Mock do Patient para teste."""
    def __init__(self):
        self.nome_completo = "Teste Validação"
        self.data_nascimento = "1990-01-01"
        self.prontuario = "TESTE-001"
        self.telefone = "(85) 99999-9999"


class MockSurgeryRequest:
    """Mock do SurgeryRequest para teste."""
    def __init__(self):
        self.ortopedista_responsavel = "Dr. Teste"
        self.procedimento_solicitado = "TESTE DE VALIDAÇÃO - IGNORAR"
        self.data_cirurgia = "2099-12-31"  # Data futura para fácil identificação
        self.diagnostico = "Teste de integração"
        self.observacoes = "Este é um teste automático. Por favor, IGNORAR."
        self.opme_ilizarov_adulto = False
        self.opme_ilizarov_infantil = False
        self.opme_caixa_35mm = True
        self.opme_placa_em_8 = False
        self.opme_hastes_im = False
        self.opme_outros = ""
        self.necessita_vaga_uti = False


def print_section(title):
    """Imprime cabeçalho de seção."""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print()


def print_status(label, status, details=""):
    """Imprime status com ícone."""
    icon = "✅" if status else "❌"
    print(f"{icon} {label}")
    if details:
        print(f"   {details}")


def main():
    """Executa validação completa."""
    parser = argparse.ArgumentParser(description='Valida integração com Google Forms')
    parser.add_argument('--skip-submit', action='store_true',
                        help='Não submete ao Forms (apenas valida config)')
    parser.add_argument('--force-refresh', action='store_true',
                        help='Força download do HTML do Forms')
    
    args = parser.parse_args()
    
    print_section("VALIDAÇÃO DE INTEGRAÇÃO COM GOOGLE FORMS")
    
    app = create_app()
    errors = 0
    
    with app.app_context():
        # =====================================================================
        # 1. VALIDAR CONFIGURAÇÕES
        # =====================================================================
        print_section("1. VALIDANDO CONFIGURAÇÕES")
        
        form_id = app.config.get('GOOGLE_FORMS_EDIT_ID')
        timeout = app.config.get('GOOGLE_FORMS_TIMEOUT', 10)
        
        if form_id:
            print_status("GOOGLE_FORMS_EDIT_ID", True, form_id)
        else:
            print_status("GOOGLE_FORMS_EDIT_ID", False, "NÃO CONFIGURADO")
            errors += 1
        
        print_status("GOOGLE_FORMS_TIMEOUT", True, f"{timeout}s")
        
        # =====================================================================
        # 2. EXTRAIR/VALIDAR ENTRY IDS
        # =====================================================================
        print_section("2. EXTRAINDO ENTRY IDS DO FORMS")
        
        if not form_id:
            print("⚠️  Pulando (FORMS_ID não configurado)")
        else:
            try:
                mapping = get_or_refresh_mapping(form_id, force_refresh=args.force_refresh)
                print_status("Extração de entry IDs", True, f"{len(mapping)} campos encontrados")
                
                print()
                print("Mapeamento:")
                for field, entry_id in mapping.items():
                    print(f"  • {field:20} → {entry_id}")
                
                # Validar campos obrigatórios
                print()
                required_fields = ["ortopedista", "procedimento", "data", "descricao", "necessita_uti"]
                missing = [f for f in required_fields if f not in mapping]
                
                if missing:
                    print_status("Campos obrigatórios", False, f"Faltando: {', '.join(missing)}")
                    errors += 1
                else:
                    print_status("Campos obrigatórios", True, "Todos presentes")
                
                if len(mapping) < 6:
                    print()
                    print("⚠️  ATENÇÃO: Menos de 6 campos encontrados!")
                    print("   Verifique se a ordem em forms_service.py está correta")
                    errors += 1
                
            except Exception as e:
                print_status("Extração de entry IDs", False, str(e))
                errors += 1
        
        # =====================================================================
        # 3. TESTAR BUILD PAYLOAD
        # =====================================================================
        print_section("3. TESTANDO CONSTRUÇÃO DE PAYLOAD")
        
        try:
            surgery = MockSurgeryRequest()
            patient = MockPatient()
            
            payload = build_forms_payload(surgery, patient)
            
            print_status("build_forms_payload()", True)
            
            print()
            print("Payload gerado:")
            print(f"  • Ortopedista: {payload['orthopedist']}")
            print(f"  • Procedimento: {payload['procedure_title']}")
            print(f"  • Data: {payload['date']}")
            print(f"  • OPME: {payload['opme']}")
            print(f"  • Necessita UTI: {payload['needs_icu']}")
            print(f"  • Descrição: {len(payload['full_description'])} caracteres")
            
            # Validar campos obrigatórios no payload
            print()
            if payload['procedure_title']:
                print_status("Campo 'procedure_title'", True)
            else:
                print_status("Campo 'procedure_title'", False, "VAZIO")
                errors += 1
            
            if payload['date']:
                print_status("Campo 'date'", True)
            else:
                print_status("Campo 'date'", False, "VAZIO")
                errors += 1
                
        except Exception as e:
            print_status("build_forms_payload()", False, str(e))
            errors += 1
        
        # =====================================================================
        # 4. TESTAR SUBMISSÃO (OPCIONAL)
        # =====================================================================
        if not args.skip_submit:
            print_section("4. TESTANDO SUBMISSÃO AO FORMS")
            
            if not form_id:
                print("⚠️  Pulando (FORMS_ID não configurado)")
            else:
                print("⚠️  ATENÇÃO: Isso criará uma resposta REAL no Google Forms!")
                print()
                print("Dados que serão enviados:")
                print(f"  • Procedimento: {payload['procedure_title']}")
                print(f"  • Data: {payload['date']}")
                print()
                
                resposta = input("Deseja continuar? (s/N): ").strip().lower()
                
                if resposta == 's':
                    try:
                        success, message, status_code = submit_form(form_id, payload, timeout)
                        
                        if success:
                            print_status("Submissão ao Forms", True, message)
                            print()
                            print("🎉 SUCESSO!")
                            print()
                            print("Próximos passos:")
                            print("  1. Abra a planilha de respostas do Forms")
                            print("  2. Verifique se nova linha foi adicionada")
                            print(f"  3. Procure por: {payload['procedure_title']}")
                            print(f"  4. Data: {payload['date']}")
                            print("  5. Aguarde alguns segundos")
                            print("  6. Verifique se evento foi criado no Google Calendar")
                            print()
                            print("  ⚠️  LEMBRE-SE DE EXCLUIR O TESTE:")
                            print("     • Resposta do Forms")
                            print("     • Evento do Calendar")
                        else:
                            print_status("Submissão ao Forms", False, message)
                            errors += 1
                            
                    except Exception as e:
                        print_status("Submissão ao Forms", False, str(e))
                        errors += 1
                else:
                    print("⏭️  Submissão pulada pelo usuário")
        else:
            print_section("4. SUBMISSÃO AO FORMS (PULADA)")
            print("Use --skip-submit=False para testar submissão real")
        
        # =====================================================================
        # RESUMO FINAL
        # =====================================================================
        print_section("RESUMO")
        
        if errors == 0:
            print("✅ TODAS AS VALIDAÇÕES PASSARAM!")
            print()
            if args.skip_submit:
                print("ℹ️  Submissão ao Forms não foi testada (--skip-submit)")
                print("   Para testar submissão real, execute:")
                print("   python scripts/validate_forms_integration.py")
            print()
            return 0
        else:
            print(f"❌ {errors} ERRO(S) ENCONTRADO(S)")
            print()
            print("Verifique os erros acima e corrija antes de continuar.")
            print()
            return 1


if __name__ == '__main__':
    sys.exit(main())
