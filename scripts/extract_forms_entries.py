"""
Script para extrair e validar entry IDs do Google Forms.

Este script:
1. Baixa o HTML do Forms público
2. Extrai os entry IDs automaticamente
3. Salva o mapeamento em cache
4. Exibe informações detalhadas para validação manual

USO:
    python scripts/extract_forms_entries.py

REQUISITOS:
    - Conexão com internet
    - ID do Forms configurado em .env (GOOGLE_FORMS_EDIT_ID)
"""

import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app import create_app
from src.services.forms_service import (
    get_public_form_html,
    extract_entry_ids,
    save_mapping_cache,
    load_mapping_cache
)


def main():
    """Extrai e valida entry IDs do Google Forms."""
    
    print("=" * 70)
    print("EXTRAÇÃO DE ENTRY IDS DO GOOGLE FORMS")
    print("=" * 70)
    print()
    
    # Criar app para obter configurações
    app = create_app()
    
    with app.app_context():
        form_id = app.config.get('GOOGLE_FORMS_EDIT_ID')
        
        if not form_id:
            print("❌ ERRO: GOOGLE_FORMS_EDIT_ID não configurado no .env")
            print()
            print("Adicione a linha:")
            print("GOOGLE_FORMS_EDIT_ID=1krid3-WpncOkRtw0oBh_2oNgdiqr5KKE6ECyxl9t_aw")
            print()
            return 1
        
        print(f"📋 ID do Forms: {form_id}")
        print()
        
        # Verificar cache existente
        print("🔍 Verificando cache existente...")
        cached_mapping = load_mapping_cache()
        
        if cached_mapping:
            print("✅ Cache encontrado!")
            print()
            print("Mapeamento em cache:")
            for field, entry_id in cached_mapping.items():
                print(f"  • {field:20} → {entry_id}")
            print()
            
            resposta = input("Deseja baixar novamente e sobrescrever? (s/N): ").strip().lower()
            if resposta != 's':
                print("Operação cancelada.")
                return 0
            print()
        
        # Baixar HTML do Forms
        print("⬇️  Baixando HTML do Google Forms...")
        try:
            html = get_public_form_html(form_id)
            print(f"✅ HTML baixado com sucesso ({len(html):,} bytes)")
            print()
        except Exception as e:
            print(f"❌ ERRO ao baixar HTML: {e}")
            print()
            print("DICAS:")
            print("  • Verifique sua conexão com a internet")
            print("  • Verifique se o Forms está público (não requer login)")
            print("  • Verifique se o ID está correto")
            return 1
        
        # Extrair entry IDs
        print("🔎 Extraindo entry IDs do HTML...")
        try:
            mapping = extract_entry_ids(html)
            print(f"✅ Extração concluída! Encontrados {len(mapping)} campos")
            print()
        except Exception as e:
            print(f"❌ ERRO ao extrair entry IDs: {e}")
            return 1
        
        # Exibir mapeamento
        print("=" * 70)
        print("MAPEAMENTO EXTRAÍDO")
        print("=" * 70)
        print()
        
        campos_esperados = {
            "ortopedista": "Ortopedista Responsável (dropdown)",
            "procedimento": "Procedimento solicitado (texto curto)",
            "data": "Data (date)",
            "descricao": "Descrição Completa (texto longo)",
            "opme": "OPME (checkbox)",
            "necessita_uti": "Necessita vaga de UTI? (radio Sim/Não)"
        }
        
        print("Campo              | Entry ID                        | Descrição")
        print("-" * 70)
        
        for field_key, description in campos_esperados.items():
            entry_id = mapping.get(field_key, "❌ NÃO ENCONTRADO")
            print(f"{field_key:18} | {entry_id:30} | {description}")
        
        # Verificar campo "Outro" do OPME
        if "opme_outro" in mapping:
            print(f"{'opme_outro':18} | {mapping['opme_outro']:30} | OPME - Outro (texto)")
        
        print()
        
        # Validar quantidade
        if len(mapping) < 6:
            print("⚠️  ATENÇÃO: Menos de 6 campos encontrados!")
            print()
            print("POSSÍVEIS CAUSAS:")
            print("  • O Forms mudou de estrutura")
            print("  • A ordem das perguntas está diferente")
            print("  • Algumas perguntas não são obrigatórias")
            print()
            print("SOLUÇÃO:")
            print("  1. Abra o Forms no navegador")
            print("  2. Inspecione o HTML (F12)")
            print("  3. Procure por 'entry.' nos inputs")
            print("  4. Ajuste o mapeamento manualmente em forms_service.py")
            print()
        else:
            print("✅ Quantidade de campos OK!")
            print()
        
        # Salvar cache
        print("💾 Salvando mapeamento em cache...")
        try:
            save_mapping_cache(mapping)
            print("✅ Cache salvo com sucesso!")
            print()
        except Exception as e:
            print(f"❌ ERRO ao salvar cache: {e}")
            return 1
        
        # Instruções finais
        print("=" * 70)
        print("PRÓXIMOS PASSOS")
        print("=" * 70)
        print()
        print("1. Valide se o mapeamento está correto:")
        print("   • Compare com a ordem das perguntas no Forms")
        print("   • Teste uma submissão real")
        print()
        print("2. Se estiver incorreto:")
        print("   • Edite src/services/forms_service.py")
        print("   • Ajuste a lista 'field_names' na função extract_entry_ids()")
        print("   • Execute este script novamente")
        print()
        print("3. Teste a integração:")
        print("   • Crie uma solicitação de cirurgia")
        print("   • Clique em 'Adicionar à Agenda'")
        print("   • Verifique se o Forms recebeu a resposta")
        print("   • Confirme se o evento foi criado no calendário")
        print()
        
        return 0


if __name__ == '__main__':
    sys.exit(main())
