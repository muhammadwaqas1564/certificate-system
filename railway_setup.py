# railway_setup.py
import os
import sys

print("=" * 60)
print("Preparing for Railway Deployment")
print("=" * 60)

# 1. Check required files
required_files = ['requirements.txt', 'Procfile', 'runtime.txt', 'app.py']
missing_files = []

for file in required_files:
    if not os.path.exists(file):
        missing_files.append(file)

if missing_files:
    print("✗ Missing files:", missing_files)
    print("Creating missing files...")
    
    for file in missing_files:
        if file == 'requirements.txt':
            with open('requirements.txt', 'w') as f:
                f.write('''Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-WTF==1.1.1
WTForms==3.0.1
email-validator==2.0.0
python-dotenv==1.0.0
Pillow==10.0.0
gunicorn==20.1.0
Werkzeug==2.3.7
psycopg2-binary==2.9.7''')
        
        elif file == 'Procfile':
            with open('Procfile', 'w') as f:
                f.write('web: gunicorn app:app')
        
        elif file == 'runtime.txt':
            with open('runtime.txt', 'w') as f:
                f.write('python-3.11.0')
        
        elif file == 'app.py':
            print("✗ app.py is missing! This is critical.")
            sys.exit(1)
        
        print(f"✓ Created {file}")

# 2. Create railway.json if not exists
if not os.path.exists('railway.json'):
    with open('railway.json', 'w') as f:
        f.write('''{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn app:app --bind 0.0.0.0:$PORT"
  }
}''')
    print("✓ Created railway.json")

# 3. Create .nixpacks.toml if not exists
if not os.path.exists('.nixpacks.toml'):
    with open('.nixpacks.toml', 'w') as f:
        f.write('''[phases.setup]
cmds = [
    "pip install -r requirements.txt"
]

[phases.install]
cmds = []

[phases.build]
cmds = []

[start]
cmd = "gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4"''')
    print("✓ Created .nixpacks.toml")

# 4. Create .env for railway
if not os.path.exists('.env'):
    with open('.env', 'w') as f:
        f.write('''# Railway Deployment Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key-change-this-in-production
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-this-password
DATABASE_URL=postgresql://postgres:password@localhost/certificate_db

# Upload Configuration
MAX_CONTENT_LENGTH=16777216
ALLOWED_EXTENSIONS=pdf,png,jpg,jpeg

# Server Configuration
HOST=0.0.0.0
PORT=8000''')
    print("✓ Created .env file (update with your values)")

# 5. Update config.py for production
print("\nUpdating config.py for production...")
config_content = '''import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///certificates.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join('uploads', 'certificates')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    
    @staticmethod
    def init_app(app):
        """Initialize app with configuration"""
        # Ensure upload directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Use PostgreSQL in production if available
    if os.environ.get('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL'].replace('postgres://', 'postgresql://')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
'''

with open('config.py', 'w') as f:
    f.write(config_content)
print("✓ Updated config.py for production")

# 6. Create .gitignore if not exists
if not os.path.exists('.gitignore'):
    with open('.gitignore', 'w') as f:
        f.write('''# Python
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

# Virtual Environment
venv/

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

# PyCharm
.idea/

# Temp files
temp/
tmp/
''')
    print("✓ Created .gitignore")

print("\n" + "=" * 60)
print("✓ Project is ready for Railway deployment!")
print("\nNext Steps:")
print("1. Create a GitHub repository for your project")
print("2. Push your code to GitHub")
print("3. Go to https://railway.app")
print("4. Sign up with GitHub")
print("5. Create new project → Deploy from GitHub repo")
print("6. Add environment variables in Railway dashboard")
print("7. Your app will be deployed automatically!")
print("=" * 60)