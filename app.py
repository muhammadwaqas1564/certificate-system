import os
import re
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from config import config
import imghdr

# Initialize extensions
db = SQLAlchemy()

# Define models here, before create_app
class Certificate(db.Model):
    __tablename__ = 'certificates'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    certificate_filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    original_filename = db.Column(db.String(255))

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

def create_app(config_name='default'):
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions with app
    db.init_app(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin_exists = User.query.filter_by(username=app.config['ADMIN_USERNAME']).first()
        if not admin_exists:
            admin_user = User(
                username=app.config['ADMIN_USERNAME'],
                password_hash=generate_password_hash(app.config['ADMIN_PASSWORD'])
            )
            db.session.add(admin_user)
            db.session.commit()
            print(f"Admin user created: {app.config['ADMIN_USERNAME']}")
    
    # Register routes
    register_routes(app)
    
    return app

def register_routes(app):
    """Register all application routes"""
    
    # Helper functions
    def allowed_file(filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    
    def validate_email(email):
        """Validate Gmail format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'
        return re.match(pattern, email) is not None
    
    def is_image_file(filepath):
        """Check if file is a valid image"""
        try:
            return imghdr.what(filepath) in ['jpeg', 'png', 'gif']
        except:
            return False
    
    # Public routes
    @app.route('/')
    def index():
        """Landing page"""
        return render_template('index.html')
    
    @app.route('/search', methods=['GET', 'POST'])
    def search_certificate():
        """Search for certificate by email"""
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            
            if not email:
                flash('Please enter an email address', 'error')
                return render_template('search.html', email=email)
            
            if not validate_email(email):
                flash('Please enter a valid Gmail address', 'error')
                return render_template('search.html', email=email)
            
            # Search for certificate
            certificate = Certificate.query.filter_by(email=email).first()
            
            if certificate:
                return redirect(url_for('preview_certificate', email=email))
            else:
                flash('No certificate found for this email address', 'error')
                return render_template('search.html', email=email)
        
        return render_template('search.html')
    
    @app.route('/preview/<email>')
    def preview_certificate(email):
        """Preview certificate"""
        certificate = Certificate.query.filter_by(email=email).first()
        
        if not certificate:
            flash('Certificate not found', 'error')
            return redirect(url_for('search_certificate'))
        
        # Determine file type
        file_ext = certificate.certificate_filename.rsplit('.', 1)[1].lower()
        is_pdf = file_ext == 'pdf'
        is_image = file_ext in ['png', 'jpg', 'jpeg']
        
        return render_template('preview.html', 
                             certificate=certificate,
                             is_pdf=is_pdf,
                             is_image=is_image)
    
    @app.route('/download/<email>')
    def download_certificate(email):
        """Download certificate"""
        certificate = Certificate.query.filter_by(email=email).first()
        
        if not certificate:
            flash('Certificate not found', 'error')
            return redirect(url_for('search_certificate'))
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], certificate.certificate_filename)
        
        if not os.path.exists(file_path):
            flash('Certificate file not found', 'error')
            return redirect(url_for('search_certificate'))
        
        # Use original filename if available, otherwise generate one
        download_name = certificate.original_filename or f"certificate_{email}.{certificate.certificate_filename.rsplit('.', 1)[1]}"
        
        return send_file(file_path, 
                        as_attachment=True,
                        download_name=download_name)
    
    # Admin routes
    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        """Admin login"""
        # If already logged in, redirect to dashboard
        if session.get('admin_logged_in'):
            return redirect(url_for('admin_dashboard'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            # Check credentials against User table
            user = User.query.filter_by(username=username).first()
            
            if user and check_password_hash(user.password_hash, password):
                session['admin_logged_in'] = True
                session.permanent = True
                flash('Login successful!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid credentials', 'error')
        
        return render_template('admin_login.html')
    
    @app.route('/admin/logout')
    def admin_logout():
        """Admin logout"""
        session.pop('admin_logged_in', None)
        flash('Logged out successfully', 'success')
        return redirect(url_for('admin_login'))
    
    def admin_required(f):
        """Decorator to require admin authentication"""
        from functools import wraps
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('admin_logged_in'):
                flash('Please login to access admin panel', 'error')
                return redirect(url_for('admin_login'))
            return f(*args, **kwargs)
        return decorated_function
    
    @app.route('/admin/dashboard')
    @admin_required
    def admin_dashboard():
        """Admin dashboard"""
        certificates = Certificate.query.order_by(Certificate.upload_date.desc()).all()
        total_certificates = len(certificates)
        
        return render_template('admin_dashboard.html', 
                             certificates=certificates,
                             total=total_certificates)
    
    @app.route('/admin/upload', methods=['GET', 'POST'])
    @admin_required
    def admin_upload():
        """Bulk upload certificates"""
        if request.method == 'POST':
            # Check if files were uploaded
            if 'certificates' not in request.files:
                flash('No files selected', 'error')
                return redirect(request.url)
            
            files = request.files.getlist('certificates')
            successful_uploads = 0
            failed_uploads = []
            
            for file in files:
                if file and file.filename != '':
                    if not allowed_file(file.filename):
                        failed_uploads.append(f"{file.filename}: Invalid file type. Allowed: PDF, PNG, JPG, JPEG")
                        continue
                    
                    try:
                        # Get original filename
                        original_filename = file.filename
                        
                        # Get file extension
                        file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
                        
                        # Extract email from filename
                        # The filename should be in format: email.extension
                        # For example: waqas@gmail.com.png
                        if '.' in original_filename:
                            # Remove extension to get email
                            email_without_ext = original_filename.rsplit('.', 1)[0]
                        else:
                            # No extension found
                            failed_uploads.append(f"{original_filename}: File must have an extension (e.g., .pdf, .png, .jpg)")
                            continue
                        
                        email = email_without_ext.lower()
                        
                        print(f"DEBUG: Processing {original_filename}")
                        print(f"DEBUG: Email extracted: {email}")
                        print(f"DEBUG: File extension: {file_ext}")
                        
                        # Validate email format
                        if not validate_email(email):
                            failed_uploads.append(f"{original_filename}: Invalid Gmail address. Must be like 'example@gmail.com'")
                            continue
                        
                        # Validate file extension
                        if file_ext not in app.config['ALLOWED_EXTENSIONS']:
                            failed_uploads.append(f"{original_filename}: Invalid file extension. Allowed: {', '.join(app.config['ALLOWED_EXTENSIONS'])}")
                            continue
                        
                        # Secure filename (preserve original name)
                        secure_name = secure_filename(original_filename)
                        
                        # Check if certificate already exists for this email
                        existing = Certificate.query.filter_by(email=email).first()
                        if existing:
                            print(f"DEBUG: Updating existing certificate for {email}")
                            # Update existing certificate
                            existing.certificate_filename = secure_name
                            existing.original_filename = original_filename
                            existing.upload_date = datetime.utcnow()
                        else:
                            print(f"DEBUG: Creating new certificate for {email}")
                            # Create new certificate record
                            certificate = Certificate(
                                email=email,
                                certificate_filename=secure_name,
                                original_filename=original_filename
                            )
                            db.session.add(certificate)
                        
                        # Ensure upload directory exists
                        upload_dir = app.config['UPLOAD_FOLDER']
                        os.makedirs(upload_dir, exist_ok=True)
                        
                        # Save file
                        file_path = os.path.join(upload_dir, secure_name)
                        print(f"DEBUG: Saving to: {file_path}")
                        file.save(file_path)
                        
                        # Verify file was saved
                        if os.path.exists(file_path):
                            file_size = os.path.getsize(file_path)
                            print(f"DEBUG: File saved successfully. Size: {file_size} bytes")
                            successful_uploads += 1
                        else:
                            error_msg = f"{original_filename}: Failed to save file"
                            print(f"DEBUG: {error_msg}")
                            failed_uploads.append(error_msg)
                        
                    except Exception as e:
                        error_msg = f"{original_filename}: {str(e)}"
                        print(f"ERROR: {error_msg}")
                        import traceback
                        traceback.print_exc()
                        failed_uploads.append(error_msg)
            
            # Commit all changes
            try:
                db.session.commit()
                print(f"DEBUG: Database commit successful")
            except Exception as e:
                db.session.rollback()
                error_msg = f"Database error: {str(e)}"
                print(f"ERROR: {error_msg}")
                failed_uploads.append(error_msg)
            
            # Show results
            if successful_uploads > 0:
                flash(f'Successfully uploaded {successful_uploads} certificate(s)', 'success')
            
            if failed_uploads:
                # Show all errors
                for error in failed_uploads:
                    flash(error, 'error')
            
            return redirect(url_for('admin_dashboard'))
        
        return render_template('upload.html')

    @app.route('/admin/delete/<int:certificate_id>', methods=['POST'])
    @admin_required
    def admin_delete(certificate_id):
        """Delete a certificate"""
        certificate = Certificate.query.get_or_404(certificate_id)
        
        try:
            # Delete file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], certificate.certificate_filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
            
            # Delete database record
            db.session.delete(certificate)
            db.session.commit()
            
            flash('Certificate deleted successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting certificate: {str(e)}', 'error')
            print(f"Delete error: {e}")
        
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/replace/<int:certificate_id>', methods=['POST'])
    @admin_required
    def admin_replace(certificate_id):
        """Replace a certificate file"""
        certificate = Certificate.query.get_or_404(certificate_id)
        
        if 'certificate_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('admin_dashboard'))
        
        file = request.files['certificate_file']
        
        if file and file.filename != '':
            if not allowed_file(file.filename):
                flash('Invalid file type. Allowed: PDF, PNG, JPG, JPEG', 'error')
                return redirect(url_for('admin_dashboard'))
            
            try:
                # Delete old file
                old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], certificate.certificate_filename)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
                    print(f"Deleted old file: {old_file_path}")
                
                # Save new file with secure filename
                filename = secure_filename(file.filename)
                
                # Ensure the filename contains the email
                if certificate.email not in filename:
                    # Add email to filename to maintain consistency
                    name, ext = os.path.splitext(filename)
                    filename = f"{certificate.email}{ext}"
                
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                print(f"Saved new file: {file_path}")
                
                # Update database
                certificate.certificate_filename = filename
                certificate.original_filename = file.filename
                certificate.upload_date = datetime.utcnow()
                db.session.commit()
                
                flash('Certificate replaced successfully', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error replacing certificate: {str(e)}', 'error')
                print(f"Replace error: {e}")
        
        return redirect(url_for('admin_dashboard'))
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    return app



# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)