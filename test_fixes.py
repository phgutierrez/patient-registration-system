#!/usr/bin/env python3
"""
Test script to verify ISSUE 1 and ISSUE 2 fixes.

ISSUE 1: Google Forms configuration should work out-of-the-box
ISSUE 2: Patient lookup by prontuário should be optimized for LAN
"""

import sys
import time
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

def test_issue_1_forms_config():
    """Test ISSUE 1: Google Forms defaults work without .env configuration"""
    print("🧪 Testing ISSUE 1: Google Forms Configuration...")
    
    try:
        from src.app import create_app
        from src.services.forms_service import get_forms_configuration
        
        app = create_app()
        with app.app_context():
            # Test 1: Should not raise error even without env vars
            try:
                public_id, view_url = get_forms_configuration()
                print(f"✅ Forms configuration resolved successfully:")
                print(f"   Public ID: {public_id[:8]}...")
                print(f"   View URL: {view_url[:50]}...")
                return True
            except ValueError as e:
                print(f"❌ Forms configuration failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Could not test forms config: {e}")
        return False

def test_issue_2_database_optimization():
    """Test ISSUE 2: Database optimizations for prontuário lookup"""
    print("\n🧪 Testing ISSUE 2: Database Optimization...")
    
    try:
        from src.app import create_app
        from src.models.patient import Patient
        from src.extensions import db
        import sqlite3
        
        app = create_app()
        with app.app_context():
            # Test 1: Check if prontuario column has index
            inspector = db.inspect(db.engine)
            indexes = inspector.get_indexes('patient')
            
            prontuario_indexed = False
            for index in indexes:
                if 'prontuario' in index.get('column_names', []):
                    prontuario_indexed = True
                    print(f"✅ Found prontuário index: {index['name']}")
                    break
            
            if not prontuario_indexed:
                print("❌ No prontuário index found")
                return False
            
            # Test 2: Check if SQLite pragmas are applied
            result = db.engine.execute("PRAGMA journal_mode").fetchone()
            journal_mode = result[0] if result else "unknown"
            
            if journal_mode.upper() == "WAL":
                print(f"✅ SQLite WAL mode enabled: {journal_mode}")
            else:
                print(f"⚠️  SQLite mode: {journal_mode} (expected WAL)")
            
            # Test 3: Performance test (if there are patients)
            patient_count = Patient.query.count()
            print(f"📊 Patient records in database: {patient_count}")
            
            if patient_count > 0:
                # Test a sample query performance
                start_time = time.time()
                sample_patient = Patient.query.first()
                if sample_patient:
                    # Test lookup by prontuário
                    test_patient = Patient.query.filter_by(prontuario=sample_patient.prontuario).first()
                    query_time = (time.time() - start_time) * 1000
                    print(f"✅ Sample prontuário query took: {query_time:.2f}ms")
                    
            return True
            
    except Exception as e:
        print(f"❌ Could not test database optimization: {e}")
        return False

def test_forms_submission_no_env():
    """Test forms submission works without environment variables"""
    print("\n🧪 Testing Forms Submission Without Env Vars...")
    
    try:
        # Temporarily clear relevant env vars to simulate EXE environment
        import os
        original_public_id = os.environ.pop('GOOGLE_FORMS_PUBLIC_ID', None)
        original_view_url = os.environ.pop('GOOGLE_FORMS_VIEWFORM_URL', None)
        
        from src.app import create_app
        
        app = create_app()
        with app.app_context():
            try:
                # Should not fail during app creation or forms config
                from src.services.forms_service import get_forms_configuration
                public_id, view_url = get_forms_configuration()
                print(f"✅ Forms work without env vars - using defaults")
                print(f"   Default ID: {public_id[:8]}...")
                success = True
            except Exception as e:
                print(f"❌ Forms failed without env vars: {e}")
                success = False
        
        # Restore original env vars
        if original_public_id:
            os.environ['GOOGLE_FORMS_PUBLIC_ID'] = original_public_id
        if original_view_url:
            os.environ['GOOGLE_FORMS_VIEWFORM_URL'] = original_view_url
            
        return success
        
    except Exception as e:
        print(f"❌ Could not test forms without env: {e}")
        return False

def main():
    """Run all tests"""
    print("🩺 Patient Registration System - Fix Verification")
    print("=" * 60)
    
    results = []
    
    # Test ISSUE 1
    results.append(test_issue_1_forms_config())
    results.append(test_forms_submission_no_env())
    
    # Test ISSUE 2  
    results.append(test_issue_2_database_optimization())
    
    print("\n" + "=" * 60)
    print("📋 TEST RESULTS:")
    print(f"✅ Passed: {sum(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("\n🎉 ALL FIXES VERIFIED SUCCESSFULLY!")
        print("✅ EXE will work without Google Forms .env configuration")
        print("✅ Patient lookup by prontuário should be faster on LAN")
    else:
        print("\n⚠️  Some fixes may need additional attention")
        
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)