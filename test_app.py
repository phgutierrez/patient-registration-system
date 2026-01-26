"""
Script de teste para verificar se a aplicação inicia corretamente
"""
import sys
import os
import logging

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Testa se todos os imports funcionam"""
    logger.info("Testando imports...")
    
    try:
        logger.info("  - Importando Flask...")
        from flask import Flask
        logger.info("  ✓ Flask OK")
        
        logger.info("  - Importando SQLAlchemy...")
        from flask_sqlalchemy import SQLAlchemy
        logger.info("  ✓ SQLAlchemy OK")
        
        logger.info("  - Importando src.config...")
        from src.config import Config
        logger.info("  ✓ Config OK")
        
        logger.info("  - Importando src.extensions...")
        from src.extensions import db, login_manager, csrf, migrate
        logger.info("  ✓ Extensions OK")
        
        logger.info("  - Importando src.app...")
        from src.app import app
        logger.info("  ✓ App OK")
        
        return True
    except Exception as e:
        logger.error(f"  ✗ Erro: {e}", exc_info=True)
        return False

def test_app_context():
    """Testa se o contexto da aplicação funciona"""
    logger.info("\nTestando contexto da aplicação...")
    
    try:
        from src.app import app
        
        with app.app_context():
            logger.info("  - Contexto criado")
            from src.extensions import db
            
            # Tentar criar tabelas
            logger.info("  - Criando tabelas...")
            db.create_all()
            logger.info("  ✓ Tabelas criadas")
            
        return True
    except Exception as e:
        logger.error(f"  ✗ Erro: {e}", exc_info=True)
        return False

def test_routes():
    """Testa se as rotas foram registradas"""
    logger.info("\nTestando rotas...")
    
    try:
        from src.app import app
        
        with app.app_context():
            rules = list(app.url_map.iter_rules())
            logger.info(f"  - Total de rotas: {len(rules)}")
            
            for rule in rules:
                logger.info(f"    • {rule.endpoint}: {rule.rule}")
            
        return True
    except Exception as e:
        logger.error(f"  ✗ Erro: {e}", exc_info=True)
        return False

def main():
    """Executa todos os testes"""
    logger.info("=" * 60)
    logger.info("TESTE DE INICIALIZAÇÃO DA APLICAÇÃO")
    logger.info("=" * 60)
    
    results = {
        'imports': test_imports(),
        'context': test_app_context(),
        'routes': test_routes()
    }
    
    logger.info("\n" + "=" * 60)
    logger.info("RESULTADOS:")
    logger.info("=" * 60)
    
    for test_name, result in results.items():
        status = "✓ PASSOU" if result else "✗ FALHOU"
        logger.info(f"  {test_name.upper()}: {status}")
    
    all_passed = all(results.values())
    logger.info("=" * 60)
    
    if all_passed:
        logger.info("✓ TODOS OS TESTES PASSARAM!")
        logger.info("\nA aplicação deve funcionar corretamente.")
        return 0
    else:
        logger.error("✗ ALGUNS TESTES FALHARAM!")
        logger.error("\nVerifique os erros acima.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
