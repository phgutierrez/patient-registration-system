from src.app import create_app, db
from src.models.user import User

def init_db():
    app = create_app()
    
    with app.app_context():
        # Drop all existing tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        # Create admin user
        admin = User(
            username='admin',
            password='admin123',
            role='administrador'
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print('✅ Database initialized successfully!')
        print('👤 Admin user created:')
        print('   Username: admin')
        print('   Password: admin123')

if __name__ == '__main__':
    init_db()