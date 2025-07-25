from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from forms import LoginForm, RegistrationForm, PasswordResetRequestForm, PasswordResetForm
from models import User, ActionLog
from models import db
from flask import current_app
from flask_mail import Message
from utils import log_action
# from config_loader import ConfigLoader  # Removed - not needed
from datetime import datetime, timedelta
import requests
import secrets
import hashlib

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Check if login is enabled
    if not ConfigLoader.is_login_enabled():
        flash('Login is currently disabled. Please contact support.', 'error')
        return redirect(url_for('index'))
    
    if current_user.is_authenticated:
        return redirect(url_for('tools.dashboard'))
    
    # Check for brute force attacks
    ip_address = request.remote_addr
    recent_failed_attempts = ActionLog.query.filter(
        ActionLog.action == 'failed_login',
        ActionLog.ip_address == ip_address,
        ActionLog.timestamp >= datetime.utcnow() - timedelta(minutes=15)
    ).count()
    
    if recent_failed_attempts >= 5:
        flash('Too many failed login attempts. Please try again in 15 minutes.', 'error')
        log_action(None, 'blocked_login', f'IP blocked due to multiple failed attempts: {ip_address}', 
                  ip_address, request.user_agent.string)
        return render_template('auth/login.html', form=LoginForm())
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                return render_template('auth/login.html', form=form)
            
            # Check for suspicious login patterns
            last_login_ip = user.last_login_ip
            current_ip = request.remote_addr
            
            if last_login_ip and last_login_ip != current_ip:
                log_action(user.id, 'login_new_ip', f'Login from new IP: {current_ip} (previous: {last_login_ip})', 
                          current_ip, request.user_agent.string)
            
            # Update user login info
            user.last_login_ip = current_ip
            user.last_login_at = datetime.utcnow()
            db.session.commit()
            
            login_user(user, remember=form.remember_me.data)
            log_action(user.id, 'login', 'User logged in successfully', request.remote_addr, request.user_agent.string)
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('tools.dashboard')
            return redirect(next_page)
        else:
            flash('Invalid email or password', 'error')
            log_action(None, 'failed_login', f'Failed login attempt for {form.email.data}', 
                      request.remote_addr, request.user_agent.string)
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Check if user registration is enabled
    if not ConfigLoader.is_user_registration_enabled():
        flash('User registration is currently disabled. Please contact support.', 'error')
        return redirect(url_for('auth.login'))
    
    if current_user.is_authenticated:
        return redirect(url_for('tools.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Generate username from email prefix
        username = form.email.data.split('@')[0]
        
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            username=username
        )
        user.set_password(form.password.data)
        
        # Generate email verification token
        token = user.generate_email_verification_token()
        
        db.session.add(user)
        db.session.commit()
        
        # Send verification email
        send_verification_email(user, token)
        
        log_action(user.id, 'register', 'User registered', request.remote_addr, request.user_agent.string)
        
        flash('Registration successful! Please check your email to verify your account.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/resend-verification')
@login_required
def resend_verification():
    if current_user.email_verified:
        flash('Your email is already verified.', 'info')
        return redirect(url_for('tools.dashboard'))
    
    # Generate new verification token
    token = current_user.generate_email_verification_token()
    db.session.commit()
    
    # Send verification email
    send_verification_email(current_user, token)
    
    flash('Verification email has been sent to your email address.', 'success')
    return redirect(url_for('tools.dashboard'))

@auth_bp.route('/change-email', methods=['POST'])
@login_required
def change_email():
    if current_user.email_verified:
        flash('Cannot change email for verified accounts.', 'error')
        return redirect(url_for('tools.dashboard'))
    
    new_email = request.form.get('new_email')
    
    if not new_email:
        flash('Please provide a valid email address.', 'error')
        return redirect(url_for('tools.dashboard'))
    
    # Check if email already exists
    existing_user = User.query.filter_by(email=new_email).first()
    if existing_user and existing_user.id != current_user.id:
        flash('This email address is already registered.', 'error')
        return redirect(url_for('tools.dashboard'))
    
    # Update email
    current_user.email = new_email
    current_user.email_verified = False  # Reset verification status
    db.session.commit()
    
    # Send new verification email
    token = current_user.generate_email_verification_token()
    db.session.commit()
    send_verification_email(current_user, token)
    
    flash(f'Email updated to {new_email}. Please verify your new email address.', 'success')
    return redirect(url_for('tools.dashboard'))

@auth_bp.route('/logout')
@login_required
def logout():
    log_action(current_user.id, 'logout', 'User logged out', request.remote_addr, request.user_agent.string)
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/verify_email/<token>')
def verify_email(token):
    user = User.query.filter_by(email_verification_token=token).first()
    if user:
        user.email_verified = True
        user.email_verification_token = None
        db.session.commit()
        flash('Email verified successfully! You can now log in.', 'success')
        log_action(user.id, 'email_verified', 'Email verified', request.remote_addr, request.user_agent.string)
    else:
        flash('Invalid or expired verification token.', 'error')
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_password_reset_token()
            db.session.commit()
            send_password_reset_email(user, token)
            log_action(user.id, 'password_reset_request', 'Password reset requested', 
                      request.remote_addr, request.user_agent.string)
        
        flash('If an account with that email exists, you will receive password reset instructions.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form)

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    user = User.query.filter_by(password_reset_token=token).first()
    if not user or user.password_reset_expires < datetime.utcnow():
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('auth.reset_password_request'))
    
    form = PasswordResetForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.password_reset_token = None
        user.password_reset_expires = None
        db.session.commit()
        
        log_action(user.id, 'password_reset', 'Password reset completed', 
                  request.remote_addr, request.user_agent.string)
        
        flash('Your password has been reset successfully!', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form, token=token)

def send_verification_email(user, token):
    """Send email verification email"""
    try:
        msg = Message(
            'Verify Your Email - KDP Tools',
            recipients=[user.email]
        )
        
        verification_url = url_for('auth.verify_email', token=token, _external=True)
        
        msg.html = f"""
        <h2>Welcome to KDP Tools!</h2>
        <p>Hi {user.first_name},</p>
        <p>Thank you for registering with KDP Tools. Please click the link below to verify your email address:</p>
        <p><a href="{verification_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
        <p>If you didn't create an account, please ignore this email.</p>
        <p>Best regards,<br>KDP Tools Team</p>
        """
        
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send verification email: {e}")

def send_password_reset_email(user, token):
    """Send password reset email"""
    try:
        msg = Message(
            'Password Reset - KDP Tools',
            recipients=[user.email]
        )
        
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        
        msg.html = f"""
        <h2>Password Reset Request</h2>
        <p>Hi {user.first_name},</p>
        <p>You requested a password reset for your KDP Tools account. Click the link below to reset your password:</p>
        <p><a href="{reset_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
        <p>This link will expire in 1 hour.</p>
        <p>If you didn't request this reset, please ignore this email.</p>
        <p>Best regards,<br>KDP Tools Team</p>
        """
        
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send password reset email: {e}")

def get_location_data():
    """Get user's location data from IP"""
    try:
        response = requests.get('http://ip-api.com/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                return {
                    'country': data.get('country', ''),
                    'city': data.get('city', ''),
                    'region': data.get('regionName', '')
                }
    except:
        pass
    return None
