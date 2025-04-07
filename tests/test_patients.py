import unittest
from datetime import datetime
from src.app import app, db
from src.models.patient import Patient

class TestPatient(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
            
    def test_create_patient(self):
        with app.app_context():
            patient_data = {
                'nome': 'Test Patient',
                'data_nascimento': '1990-01-01',
                'cns': '123456789012345',
                'nome_mae': 'Test Mother',
                'cidade': 'Test City',
                'endereco': 'Test Address',
                'estado': 'SP'
            }
            patient = Patient.from_dict(patient_data)
            db.session.add(patient)
            db.session.commit()
            
            saved_patient = Patient.query.first()
            self.assertEqual(saved_patient.nome, 'Test Patient')

if __name__ == '__main__':
    unittest.main()