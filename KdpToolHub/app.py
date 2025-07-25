import os
import logging
from datetime import datetime
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# db will be imported from models
login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Database configuration - External MySQL
    mysql_url = os.environ.get("DATABASE_URL", "mysql+pymysql://userkdpdbs:97dccde968@db4free.net:3306/kdpdbs")
    app.config["SQLALCHEMY_DATABASE_URI"] = mysql_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_timeout": 20,
        "pool_size": 10,
        "max_overflow": 20
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Mail configuration for Gmail SMTP
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')
    
    # Import db from models
    from models import db
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Config injection removed - using direct template variables
    
    # Maintenance mode middleware
    @app.before_request
    def check_maintenance_mode():
        from flask import request, render_template
        from flask_login import current_user
        
        # Skip maintenance check for admin users and specific routes
        if (current_user.is_authenticated and current_user.is_admin) or \
           request.endpoint in ['static', 'admin.login', 'admin.dashboard'] or \
           request.path.startswith('/admin'):
            return None
        
        # Check if maintenance mode is enabled
        if ConfigLoader.is_maintenance_mode():
            maintenance_data = ConfigLoader.get_maintenance_data()
            return render_template('maintenance.html', 
                                 maintenance_data=maintenance_data,
                                 site_name=ConfigLoader.get_site_name(),
                                 contact_email=ConfigLoader.get_contact_email(),
                                 primary_color=ConfigLoader.get_primary_color(),
                                 secondary_color=ConfigLoader.get_secondary_color(),
                                 favicon_url=ConfigLoader.get_favicon_url()), 503
    
    # Add custom Jinja2 filters
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """Convert newlines to <br> tags"""
        if text:
            return text.replace('\n', '<br>')
        return text
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from auth import auth_bp
    from google_auth import google_auth
    from tools import tools_bp
    from admin import admin_bp
    from payments import payments_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(google_auth)
    app.register_blueprint(tools_bp, url_prefix='/tools')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(payments_bp, url_prefix='/payments')
    
    # Main routes
    from flask import render_template, request
    from flask_login import current_user
    from models import User, ToolUsage
    from datetime import datetime
    import json
    
    @app.route('/')
    def index():
        # Log visit
        if current_user.is_authenticated:
            from utils import log_action
            log_action(current_user.id, 'page_visit', 'index', request.remote_addr, request.user_agent.string)
        
        # Get available tools using Tools Manager
        from tools_manager import ToolsManager
        available_tools = ToolsManager.get_tools_with_status(current_user if current_user.is_authenticated else None)
        
        return render_template('index.html', available_tools=available_tools)
    
    @app.route('/contact')
    def contact():
        from forms import ContactForm
        form = ContactForm()
        return render_template('contact.html', form=form)
    
    @app.route('/plans')
    def plans():
        return render_template('subscription/plans.html')
    
    @app.route('/about')
    def about():
        return render_template('about.html')
    
    @app.route('/subscription-preview')
    def subscription_preview():
        return render_template('subscription_preview.html')
    
    # Initialize database tables only
    with app.app_context():
        import models  # noqa: F401
        db.create_all()
    
    return app

# Create app instance
app = create_app()

# Export db for external scripts
from models import db
