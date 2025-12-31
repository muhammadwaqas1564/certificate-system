# setup_render.py
import os
import secrets

print("=" * 60)
print("🚀 RENDER.COM DEPLOYMENT SETUP")
print("=" * 60)

# Generate secure credentials
secret_key = secrets.token_hex(32)
admin_password = secrets.token_hex(16)

print("\n📁 Creating deployment files...")

# 1. Create render.yaml
render_config = '''services:
  - type: web
    name: certificate-system
    runtime: python
    region: oregon  # Options: oregon, frankfurt, singapore
    plan: free
    buildCommand: "pip install -r requirements.txt"
    startCommand: "gunicorn app:app"
    envVars:
      - key: FLASK_ENV
        value: production
      - key: PYTHON_VERSION
        value: 3.11.0
    disk:
      name: uploads
      mountPath: /opt/render/project/src/uploads
      sizeGB: 1
'''

with open('render.yaml', 'w') as f:
    f.write(render_config)
print("✅ Created render.yaml")

# 2. Create requirements.txt
requirements = '''Flask==2.3.3
Flask-SQLAlchemy==3.0.5
gunicorn==21.2.0
Werkzeug==3.0.1
Pillow==10.1.0
python-dotenv==1.0.0
psycopg2-binary==2.9.9
email-validator==2.0.0
'''

with open('requirements.txt', 'w') as f:
    f.write(requirements)
print("✅ Created requirements.txt")

# 3. Create Procfile
with open('Procfile', 'w') as f:
    f.write('web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4')
print("✅ Created Procfile")

# 4. Create runtime.txt
with open('runtime.txt', 'w') as f:
    f.write('python-3.11.0')
print("✅ Created runtime.txt")

# 5. Create .env.example with your generated credentials
env_content = f'''# Render Deployment Configuration
# COPY THIS TO .env FILE AND UPDATE VALUES

# Flask Configuration
FLASK_ENV=production
SECRET_KEY={secret_key}

# Admin Credentials (CHANGE THESE!)
ADMIN_USERNAME=admin
ADMIN_PASSWORD={admin_password}

# Database (Render will provide DATABASE_URL automatically)
# DATABASE_URL will be auto-set by Render PostgreSQL

# File Upload Settings
MAX_CONTENT_LENGTH=16777216  # 16MB
ALLOWED_EXTENSIONS=pdf,png,jpg,jpeg

# Server Settings
PORT=10000
HOST=0.0.0.0

# Application Settings
UPLOAD_FOLDER=uploads/certificates
'''

with open('.env.example', 'w') as f:
    f.write(env_content)
print("✅ Created .env.example")

# 6. Create .gitignore if not exists
if not os.path.exists('.gitignore'):
    gitignore = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Flask
instance/
*.db
*.sqlite3

# Uploads (but keep empty folder structure)
uploads/certificates/*

# Environment variables
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log

# Coverage
.coverage
htmlcov/
'''
    with open('.gitignore', 'w') as f:
        f.write(gitignore)
    print("✅ Created .gitignore")

# 7. Update config.py for Render
config_content = '''import os
from datetime import timedelta
from urllib.parse import urlparse

class Config:
    """Base configuration for Render"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database configuration for Render
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Render provides DATABASE_URL, convert postgres:// to postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        # Fallback to SQLite for local development
        SQLALCHEMY_DATABASE_URI = 'sqlite:///certificates.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_recycle': 300}
    
    # File upload configuration
    UPLOAD_FOLDER = os.path.join('uploads', 'certificates')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    
    # Admin credentials
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_COOKIE_SECURE = True  # Use secure cookies in production
    SESSION_COOKIE_HTTPONLY = True
    
    @staticmethod
    def init_app(app):
        """Initialize app with configuration"""
        # Ensure upload directory exists
        upload_path = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_path, exist_ok=True)
        
        # Create uploads directory structure
        os.makedirs('uploads/certificates', exist_ok=True)
        
        print(f"✅ Upload folder configured at: {upload_path}")
        print(f"✅ Database URI: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # Production-specific settings
    PREFERRED_URL_SCHEME = 'https'
    
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        """Override database URI for production"""
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            return database_url
        return super().SQLALCHEMY_DATABASE_URI


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
'''

with open('config.py', 'w') as f:
    f.write(config_content)
print("✅ Updated config.py for Render")

# 8. Update app.py for production
print("\n📝 Checking app.py for production readiness...")

# Read current app.py
with open('app.py', 'r') as f:
    app_content = f.read()

# Ensure production config is used
if 'create_app(config_name=\'production\')' not in app_content:
    # Find the app creation line
    if 'app = create_app()' in app_content:
        app_content = app_content.replace(
            'app = create_app()',
            '# Use production config on Render\nif os.environ.get("RENDER"):\n    app = create_app("production")\nelse:\n    app = create_app()'
        )
    elif 'app = create_app(config_name=' not in app_content:
        # Add at the end before if __name__ block
        lines = app_content.split('\n')
        new_lines = []
        for line in lines:
            if line.strip() == 'if __name__ == \'__main__\':':
                new_lines.append('# Use production config on Render')
                new_lines.append('if os.environ.get("RENDER") or os.environ.get("FLASK_ENV") == "production":')
                new_lines.append('    app = create_app("production")')
                new_lines.append('else:')
                new_lines.append('    app = create_app()')
                new_lines.append('')
            new_lines.append(line)
        app_content = '\n'.join(new_lines)
    
    with open('app.py', 'w') as f:
        f.write(app_content)
    print("✅ Updated app.py for production")

# 9. Create directories
os.makedirs('uploads/certificates', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('static/images', exist_ok=True)
print("✅ Created required directories")

print("\n" + "=" * 60)
print("✅ SETUP COMPLETE!")
print("=" * 60)

print("\n📋 YOUR DEPLOYMENT CREDENTIALS:")
print("-" * 40)
print(f"🔐 Secret Key: {secret_key}")
print(f"👤 Admin Username: admin")
print(f"🔑 Admin Password: {admin_password}")
print("-" * 40)
print("⚠️  IMPORTANT: Change admin password after deployment!")

print("\n🚀 NEXT STEPS:")
print("=" * 60)
print("1. Review the created files")
print("2. Rename '.env.example' to '.env'")
print("3. Update .env with your actual values")
print("4. Push to GitHub:")
print("   git add .")
print("   git commit -m 'Ready for Render deployment'")
print("   git push origin main")
print("")
print("5. DEPLOY ON RENDER:")
print("   a. Go to: https://render.com")
print("   b. Sign up with GitHub")
print("   c. Click 'New +' → 'Web Service'")
print("   d. Connect your GitHub repository")
print("   e. Fill in the deployment form")
print("   f. Add PostgreSQL database")
print("   g. Add environment variables")
print("   h. Deploy!")
print("")
print("🌐 Your app will be live at:")
print("   https://certificate-system.onrender.com")
print("=" * 60)

print("\n⚙️  RENDER DEPLOYMENT FORM SETTINGS:")
print("-" * 40)
print("Name: certificate-system")
print("Environment: Python 3")
print("Build Command: pip install -r requirements.txt")
print("Start Command: gunicorn app:app")
print("Plan: Free")
print("Region: Oregon (or choose closest to you)")
print("-" * 40)