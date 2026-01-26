"""
Script para atualizar todos os templates com o novo padrão visual
"""
import os
import re
from pathlib import Path

def update_template(file_path):
    """Atualiza um template individual com o novo padrão visual"""
    print(f"Processando: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 1. Atualizar headers de cards bg-primary para gradiente escuro
    content = re.sub(
        r'<div class="card-header bg-primary text-white">',
        r'<div class="card-header" style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: white; border: none;">',
        content
    )
    
    # 2. Adicionar border-0 shadow-sm aos cards que não têm
    content = re.sub(
        r'<div class="card mb-4">',
        r'<div class="card mb-4 border-0 shadow-sm">',
        content
    )
    
    # 3. Atualizar cabeçalhos de página com card gradiente azul
    # Padrão: <div class="d-flex justify-content-between align-items-center mb-4">
    #         <h1>TÍTULO</h1>
    # Para cabeçalhos de editar/visualizar paciente
    if 'Editar Paciente' in content or 'Detalhes do Paciente' in content:
        # Substituir o cabeçalho simples por card gradiente
        content = re.sub(
            r'<div class="d-flex justify-content-between align-items-center mb-4">\s*<h1>([^<]+)</h1>',
            r'''<div class="card border-0 shadow-sm mb-4" style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white;">
        <div class="card-body py-4">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h1 class="mb-0" style="font-size: 2rem; font-weight: 700;">
                        <i class="fas fa-user-edit me-3"></i>\1</h1>
                </div>''',
            content,
            count=1
        )
        
        # Fechar a div do card após os botões
        content = re.sub(
            r'(</div>\s*</div>\s*\n\s*<div class="alert alert-info">)',
            r'''</div>
        </div>
    </div>

    \1''',
            content,
            count=1
        )
    
    # 4. Melhorar alertas info
    content = re.sub(
        r'<div class="alert alert-info">\s*<i class="fas fa-info-circle"></i>\s*Preencha todos os campos obrigatórios \(\*\)\.\s*</div>',
        '',  # Remover pois já está no cabeçalho
        content
    )
    
    # 5. Adicionar ícones com me-2 (margin-end) aos títulos de card
    content = re.sub(
        r'<i class="fas ([^"]+)"></i>\s+',
        r'<i class="fas \1 me-2"></i>',
        content
    )
    
    # 6. Adicionar gap-3 aos botões
    content = re.sub(
        r'<div class="d-flex gap-2">',
        r'<div class="d-flex gap-3">',
        content
    )
    
    # Salvar apenas se houve mudanças
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Atualizado: {file_path}")
        return True
    else:
        print(f"⏭️  Sem mudanças: {file_path}")
        return False

def main():
    """Função principal"""
    templates_dir = Path(__file__).parent / 'src' / 'templates'
    
    # Lista de templates para atualizar (excluindo os já atualizados)
    templates_to_update = [
        'patient/edit.html',
        'patient/view.html',
        'surgery/request.html',
        'surgery/confirmation.html',
        'surgery/download.html',
        'user_registration.html',
        'dashboard.html',
        'registration.html',
        'patient_details.html',
        'surgery_request.html',
        'select_user.html'
    ]
    
    updated_count = 0
    for template in templates_to_update:
        template_path = templates_dir / template
        if template_path.exists():
            if update_template(template_path):
                updated_count += 1
        else:
            print(f"❌ Não encontrado: {template_path}")
    
    print(f"\n🎉 Concluído! {updated_count} templates atualizados.")

if __name__ == '__main__':
    main()
