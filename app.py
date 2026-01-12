from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, WireGuardConfig
from wireguard_manager import WireGuardManager
from config import Config
import io
from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== Public Routes ====================

@app.route('/')
def index():
    """Home page - redirect to appropriate dashboard"""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout current user"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# ==================== User Routes ====================

@app.route('/dashboard')
@login_required
def user_dashboard():
    """User dashboard - view and download config"""
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    return render_template('user_dashboard.html', user=current_user)

@app.route('/download-config')
@login_required
def download_config():
    """Download WireGuard configuration file"""
    if current_user.is_admin:
        flash('Admin users cannot download client configs', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    try:
        config = WireGuardManager.create_user_config(current_user)
        
        # Create a file-like object
        buffer = io.BytesIO()
        buffer.write(config.encode())
        buffer.seek(0)
        
        filename = f"{current_user.username}_wg.conf"
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='text/plain'
        )
    except Exception as e:
        flash(f'Error generating config: {str(e)}', 'danger')
        return redirect(url_for('user_dashboard'))

@app.route('/qr-code')
@login_required
def qr_code():
    """Get QR code for mobile setup"""
    if current_user.is_admin:
        return jsonify({'error': 'Admin users cannot generate QR codes'}), 403
    
    try:
        config = WireGuardManager.create_user_config(current_user)
        qr_image = WireGuardManager.generate_qr_code(config)
        
        return jsonify({'qr_code': f'data:image/png;base64,{qr_image}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== Admin Routes ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page (same as regular login)"""
    return login()

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard - manage users"""
    users = User.query.filter_by(is_admin=False).all()
    wg_config = WireGuardConfig.query.first()
    return render_template('admin_dashboard.html', users=users, wg_config=wg_config)

@app.route('/admin/add-user', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    """Add a new user"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        # Check if user exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'danger')
            return redirect(url_for('add_user'))
        
        try:
            # Create user
            user = User(
                username=username,
                email=email,
                is_admin=False
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # Generate WireGuard config
            WireGuardManager.create_user_config(user)
            
            # Update server config
            WireGuardManager.apply_server_config()
            
            flash(f'User {username} created successfully', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'danger')
    
    return render_template('add_user.html')

@app.route('/admin/edit-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit an existing user"""
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        flash('Cannot edit admin users', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        user.email = request.form.get('email')
        password = request.form.get('password')
        
        if password:
            user.set_password(password)
        
        user.is_active = request.form.get('is_active') == 'on'
        
        try:
            db.session.commit()
            
            # Update server config
            WireGuardManager.apply_server_config()
            
            flash(f'User {user.username} updated successfully', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'danger')
    
    return render_template('edit_user.html', user=user)

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user"""
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        flash('Cannot delete admin users', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    try:
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        # Update server config
        WireGuardManager.apply_server_config()
        
        flash(f'User {username} deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    """Enable/disable a user"""
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        return jsonify({'error': 'Cannot toggle admin users'}), 403
    
    try:
        user.is_active = not user.is_active
        db.session.commit()
        
        # Update server config
        WireGuardManager.apply_server_config()
        
        return jsonify({
            'success': True,
            'is_active': user.is_active
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/regenerate-config/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def regenerate_config(user_id):
    """Regenerate user's WireGuard keys and config"""
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        return jsonify({'error': 'Cannot regenerate config for admin users'}), 403
    
    try:
        # Clear existing keys
        user.wg_private_key = None
        user.wg_public_key = None
        user.wg_preshared_key = None
        
        db.session.commit()
        
        # Generate new config
        WireGuardManager.create_user_config(user)
        
        # Update server config
        WireGuardManager.apply_server_config()
        
        flash(f'Configuration regenerated for {user.username}', 'success')
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
