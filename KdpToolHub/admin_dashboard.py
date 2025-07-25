from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import (User, ToolUsage, ActionLog, AdminMessage, ToolSetting, 
                   UserToolRestriction, ContactMessage, SiteSettings, ToolPrompts,
                   UserManagement, SystemActivity, AdminActions, DynamicContent)
from app import db
from utils import log_action
from datetime import datetime, timedelta
import json
import functools
import stripe
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to require admin access"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def log_admin_action(action_type, details, target_user_id=None):
    """Log admin actions for audit trail"""
    action = AdminActions(
        admin_id=current_user.id,
        target_user_id=target_user_id,
        action_type=action_type,
        action_details=details,
        ip_address=request.remote_addr
    )
    db.session.add(action)
    db.session.commit()

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Main admin dashboard with statistics and overview"""
    # User statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    admin_users = User.query.filter_by(is_admin=True).count()
    free_users = User.query.filter_by(subscription_type='free').count()
    paid_users = User.query.filter(User.subscription_type.in_(['monthly', 'yearly'])).count()
    
    # Recent activity statistics
    today = datetime.utcnow().date()
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    new_users_today = User.query.filter(
        db.func.date(User.created_at) == today
    ).count()
    
    new_users_week = User.query.filter(User.created_at >= week_ago).count()
    
    # Tool usage statistics
    popular_tools = db.session.query(
        ToolUsage.tool_name,
        db.func.count(ToolUsage.id).label('usage_count')
    ).group_by(ToolUsage.tool_name).order_by(db.desc('usage_count')).limit(8).all()
    
    # Revenue statistics (from paid subscriptions)
    monthly_revenue = paid_users * 15  # $15 per month
    
    # System health metrics
    unread_messages = ContactMessage.query.filter_by(is_responded=False).count()
    recent_errors = SystemActivity.query.filter_by(severity='error').filter(
        SystemActivity.timestamp >= week_ago
    ).count()
    
    # Recent activities
    recent_activities = SystemActivity.query.order_by(
        SystemActivity.timestamp.desc()
    ).limit(15).all()
    
    # Recent user registrations
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'admin_users': admin_users,
        'free_users': free_users,
        'paid_users': paid_users,
        'new_users_today': new_users_today,
        'new_users_week': new_users_week,
        'popular_tools': popular_tools,
        'monthly_revenue': monthly_revenue,
        'unread_messages': unread_messages,
        'recent_errors': recent_errors
    }
    
    log_admin_action('dashboard_access', {'timestamp': datetime.utcnow().isoformat()})
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         activities=recent_activities,
                         recent_users=recent_users)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """User management interface"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    plan_filter = request.args.get('plan', '')
    status_filter = request.args.get('status', '')
    sort_by = request.args.get('sort', 'created_at')
    
    query = User.query
    
    # Apply filters
    if search:
        query = query.filter(
            db.or_(
                User.email.ilike(f'%{search}%'),
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%')
            )
        )
    
    if plan_filter:
        query = query.filter_by(subscription_type=plan_filter)
    
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    elif status_filter == 'admin':
        query = query.filter_by(is_admin=True)
    
    # Apply sorting
    if sort_by == 'email':
        query = query.order_by(User.email)
    elif sort_by == 'subscription':
        query = query.order_by(User.subscription_type.desc())
    elif sort_by == 'created_at':
        query = query.order_by(User.created_at.desc())
    
    users = query.paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/users.html', users=users, 
                         search=search, plan_filter=plan_filter, 
                         status_filter=status_filter, sort_by=sort_by)

@admin_bp.route('/user/<int:user_id>')
@login_required
@admin_required
def user_details(user_id):
    """Detailed user management page"""
    user = User.query.get_or_404(user_id)
    
    # Get user activity history
    activities = SystemActivity.query.filter_by(user_id=user_id).order_by(
        SystemActivity.timestamp.desc()
    ).limit(50).all()
    
    # Get user tool usage
    tool_usage = ToolUsage.query.filter_by(user_id=user_id).order_by(
        ToolUsage.used_at.desc()
    ).limit(20).all()
    
    # Get user restrictions
    restrictions = UserManagement.query.filter_by(
        user_id=user_id, is_active=True
    ).all()
    
    return render_template('admin/user_details.html', 
                         user=user, activities=activities, 
                         tool_usage=tool_usage, restrictions=restrictions)

@admin_bp.route('/user/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Enable/disable user account"""
    user = User.query.get_or_404(user_id)
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'enabled' if user.is_active else 'disabled'
    log_admin_action('user_status_change', {
        'user_id': user_id,
        'new_status': status,
        'user_email': user.email
    }, target_user_id=user_id)
    
    flash(f'User {user.email} has been {status}.', 'success')
    return redirect(url_for('admin.user_details', user_id=user_id))

@admin_bp.route('/user/<int:user_id>/upgrade', methods=['POST'])
@login_required
@admin_required
def upgrade_user(user_id):
    """Manually upgrade user to premium"""
    user = User.query.get_or_404(user_id)
    plan_type = request.form.get('plan_type', 'monthly')
    duration_days = 30 if plan_type == 'monthly' else 365
    
    user.subscription_type = plan_type
    user.subscription_start = datetime.utcnow()
    user.subscription_end = datetime.utcnow() + timedelta(days=duration_days)
    user.daily_usage_count = 0
    
    db.session.commit()
    
    log_admin_action('user_upgrade', {
        'user_id': user_id,
        'plan_type': plan_type,
        'user_email': user.email,
        'admin_upgrade': True
    }, target_user_id=user_id)
    
    flash(f'User {user.email} has been upgraded to {plan_type} plan.', 'success')
    return redirect(url_for('admin.user_details', user_id=user_id))

@admin_bp.route('/user/<int:user_id>/refund', methods=['POST'])
@login_required
@admin_required  
def refund_user(user_id):
    """Process refund for user"""
    user = User.query.get_or_404(user_id)
    
    if not user.stripe_customer_id:
        flash('User has no Stripe customer ID for refund.', 'error')
        return redirect(url_for('admin.user_details', user_id=user_id))
    
    try:
        # Get latest charge for this customer
        charges = stripe.Charge.list(customer=user.stripe_customer_id, limit=1)
        
        if charges.data:
            charge = charges.data[0]
            refund = stripe.Refund.create(
                charge=charge.id,
                reason='requested_by_customer'
            )
            
            # Update user subscription
            user.subscription_type = 'free'
            user.stripe_subscription_id = None
            user.subscription_end = None
            user.daily_usage_count = 0
            
            db.session.commit()
            
            log_admin_action('user_refund', {
                'user_id': user_id,
                'refund_id': refund.id,
                'amount': refund.amount / 100,
                'user_email': user.email
            }, target_user_id=user_id)
            
            flash(f'Refund processed for {user.email}. Amount: ${refund.amount / 100}', 'success')
        else:
            flash('No charges found for this user.', 'error')
            
    except stripe.error.StripeError as e:
        flash(f'Refund failed: {str(e)}', 'error')
    
    return redirect(url_for('admin.user_details', user_id=user_id))

@admin_bp.route('/settings')
@login_required
@admin_required
def site_settings():
    """Site settings management"""
    # Get all settings grouped by category
    settings = {}
    all_settings = SiteSettings.query.filter_by(is_active=True).order_by(
        SiteSettings.category, SiteSettings.setting_key
    ).all()
    
    for setting in all_settings:
        if setting.category not in settings:
            settings[setting.category] = []
        settings[setting.category].append(setting)
    
    return render_template('admin/settings.html', settings=settings)

@admin_bp.route('/settings/update', methods=['POST'])
@login_required
@admin_required
def update_settings():
    """Update site settings"""
    for key, value in request.form.items():
        if key.startswith('setting_'):
            setting_key = key.replace('setting_', '')
            setting = SiteSettings.query.filter_by(setting_key=setting_key).first()
            
            if setting:
                setting.setting_value = value
                setting.updated_by = current_user.id
                setting.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    log_admin_action('settings_update', {
        'updated_settings': list(request.form.keys()),
        'timestamp': datetime.utcnow().isoformat()
    })
    
    flash('Settings updated successfully.', 'success')
    return redirect(url_for('admin.site_settings'))

@admin_bp.route('/tools')
@login_required
@admin_required
def tools_management():
    """Tools configuration and management"""
    # Get tool settings
    tool_settings = ToolSetting.query.all()
    
    # Get tool prompts
    prompts = ToolPrompts.query.filter_by(is_active=True).order_by(
        ToolPrompts.tool_name, ToolPrompts.prompt_type
    ).all()
    
    # Group prompts by tool
    tool_prompts = {}
    for prompt in prompts:
        if prompt.tool_name not in tool_prompts:
            tool_prompts[prompt.tool_name] = []
        tool_prompts[prompt.tool_name].append(prompt)
    
    tools_list = [
        'title-generator', 'subtitle-generator', 'description-generator',
        'author-generator', 'keyword-research', 'category-finder',
        'royalty-calculator', 'trademark-search'
    ]
    
    return render_template('admin/tools.html', 
                         tool_settings=tool_settings,
                         tool_prompts=tool_prompts,
                         tools_list=tools_list)

@admin_bp.route('/tools/toggle/<tool_name>', methods=['POST'])
@login_required
@admin_required
def toggle_tool(tool_name):
    """Enable/disable a tool"""
    tool_setting = ToolSetting.query.filter_by(tool_name=tool_name).first()
    
    if not tool_setting:
        tool_setting = ToolSetting(tool_name=tool_name, is_enabled=True)
        db.session.add(tool_setting)
    
    tool_setting.is_enabled = not tool_setting.is_enabled
    db.session.commit()
    
    status = 'enabled' if tool_setting.is_enabled else 'disabled'
    log_admin_action('tool_toggle', {
        'tool_name': tool_name,
        'new_status': status
    })
    
    flash(f'Tool {tool_name} has been {status}.', 'success')
    return redirect(url_for('admin.tools_management'))

@admin_bp.route('/content')
@login_required
@admin_required
def content_management():
    """Dynamic content management"""
    content_items = DynamicContent.query.filter_by(is_active=True).order_by(
        DynamicContent.page_location, DynamicContent.content_key
    ).all()
    
    # Group by page location
    content_by_page = {}
    for item in content_items:
        if item.page_location not in content_by_page:
            content_by_page[item.page_location] = []
        content_by_page[item.page_location].append(item)
    
    return render_template('admin/content.html', content_by_page=content_by_page)

@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """Analytics and reporting dashboard"""
    # Date range filtering
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # User growth analytics
    user_growth = db.session.query(
        db.func.date(User.created_at).label('date'),
        db.func.count(User.id).label('count')
    ).filter(User.created_at >= start_date).group_by(
        db.func.date(User.created_at)
    ).order_by('date').all()
    
    # Tool usage analytics
    tool_usage_stats = db.session.query(
        ToolUsage.tool_name,
        db.func.count(ToolUsage.id).label('total_usage'),
        db.func.count(db.distinct(ToolUsage.user_id)).label('unique_users')
    ).filter(ToolUsage.used_at >= start_date).group_by(
        ToolUsage.tool_name
    ).order_by(db.desc('total_usage')).all()
    
    # Subscription analytics
    subscription_stats = db.session.query(
        User.subscription_type,
        db.func.count(User.id).label('count')
    ).group_by(User.subscription_type).all()
    
    # Revenue analytics (estimated)
    revenue_data = {
        'monthly_users': User.query.filter_by(subscription_type='monthly').count(),
        'yearly_users': User.query.filter_by(subscription_type='yearly').count(),
        'estimated_monthly_revenue': User.query.filter_by(subscription_type='monthly').count() * 15,
        'estimated_yearly_revenue': User.query.filter_by(subscription_type='yearly').count() * 150
    }
    
    return render_template('admin/analytics.html',
                         user_growth=user_growth,
                         tool_usage_stats=tool_usage_stats,
                         subscription_stats=subscription_stats,
                         revenue_data=revenue_data,
                         days=days)

@admin_bp.route('/logs')
@login_required
@admin_required
def system_logs():
    """System logs and monitoring"""
    page = request.args.get('page', 1, type=int)
    severity = request.args.get('severity', '')
    activity_type = request.args.get('type', '')
    
    query = SystemActivity.query
    
    if severity:
        query = query.filter_by(severity=severity)
    
    if activity_type:
        query = query.filter_by(activity_type=activity_type)
    
    logs = query.order_by(SystemActivity.timestamp.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    # Get admin actions
    admin_actions = AdminActions.query.order_by(
        AdminActions.timestamp.desc()
    ).limit(20).all()
    
    return render_template('admin/logs.html', 
                         logs=logs, 
                         admin_actions=admin_actions,
                         severity=severity,
                         activity_type=activity_type)