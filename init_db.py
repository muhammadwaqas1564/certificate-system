# init_db.py
from app import create_app, db
from datetime import datetime

app = create_app()

with app.app_context():
    # Drop all tables (only in development)
    db.drop_all()
    
    # Create all tables
    db.create_all()
    
    print("Database tables created successfully!")
    print("Tables created:")
    print("- certificates")
    print("- users")
    
    # Create admin user if not exists
    from app import User  # Import inside app context
    
    # Check if admin user exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        from werkzeug.security import generate_password_hash
        
        # Create admin user
        admin_user = User(
            username='admin',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created: username='admin', password='admin123'")
    
    print("\nDatabase initialization complete!")