from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import (User, ToolUsage, ActionLog, ContactMessage, ToolSetting, UserToolRestriction, 
                   WebsiteConfiguration, ToolConfiguration, MaintenanceMode)
from models import db
from utils import log_action
from datetime import datetime, timedelta
import json
import functools

admin_bp = Blueprint('admin', __name__)

class AdminStats:
    def __init__(self):
        self.unread_messages = 0

def admin_required(f):
    """Decorator to require admin access"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with comprehensive statistics"""
    
    # Basic user statistics
    total_users = User.query.count()
    paid_users = User.query.filter(User.subscription_type.in_(['monthly', 'yearly'])).count()
    
    # Recent users (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users_week = User.query.filter(User.created_at >= week_ago).count()
    
    # Today's new users
    today = datetime.utcnow().date()
    new_users_today = User.query.filter(db.func.date(User.created_at) == today).count()
    
    # Monthly revenue calculation
    monthly_revenue = paid_users * 15  # $15 per monthly subscription
    
    # Tool usage statistics
    popular_tools = db.session.query(
        ToolUsage.tool_name, 
        db.func.count(ToolUsage.id).label('usage_count')
    ).group_by(ToolUsage.tool_name).order_by(db.desc('usage_count')).limit(8).all()
    
    # Recent users for sidebar
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Recent system activities
    activities = ActionLog.query.order_by(ActionLog.timestamp.desc()).limit(10).all()
    
    # Unread messages
    unread_messages = ContactMessage.query.filter_by(is_responded=False).count()
    
    # Prepare statistics object
    stats = {
        'total_users': total_users,
        'paid_users': paid_users,
        'new_users_week': new_users_week,
        'new_users_today': new_users_today,
        'monthly_revenue': monthly_revenue,
        'popular_tools': popular_tools,
        'unread_messages': unread_messages
    }
    
    # Log admin dashboard access
    log_action(current_user.id, 'admin_dashboard_access', 'Accessed admin dashboard', 
              request.remote_addr, str(request.user_agent))
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         recent_users=recent_users, 
                         activities=activities)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """User management page with filtering and pagination"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    plan_filter = request.args.get('plan', '')
    status_filter = request.args.get('status', '')
    sort_by = request.args.get('sort', 'created_at')
    
    query = User.query
    
    # Apply search filter
    if search:
        query = query.filter(
            db.or_(
                User.first_name.contains(search),
                User.last_name.contains(search),
                User.email.contains(search)
            )
        )
    
    # Apply plan filter
    if plan_filter:
        query = query.filter(User.subscription_type == plan_filter)
    
    # Apply status filter
    if status_filter == 'active':
        query = query.filter(User.is_active.is_(True))
    elif status_filter == 'inactive':
        query = query.filter(User.is_active.is_(False))
    elif status_filter == 'admin':
        query = query.filter(User.is_admin.is_(True))
    
    # Apply sorting
    if sort_by == 'email':
        query = query.order_by(User.email)
    elif sort_by == 'subscription':
        query = query.order_by(User.subscription_type.desc())
    else:  # default to created_at
        query = query.order_by(User.created_at.desc())
    
    # Paginate results
    users = query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Log admin users access
    log_action(current_user.id, 'admin_users_access', 'Accessed user management', 
              request.remote_addr, str(request.user_agent))
    
    return render_template('admin/users.html', 
                         users=users,
                         search=search,
                         plan_filter=plan_filter,
                         status_filter=status_filter,
                         sort_by=sort_by,
                         now=datetime.utcnow())

@admin_bp.route('/tools')
@login_required
@admin_required  
def tools_management():
    """Tools management and configuration page"""
    
    # List of all available tools
    tools_list = [
        'title-generator', 'subtitle-generator', 'description-generator',
        'author-generator', 'keyword-research', 'category-finder',
        'royalty-calculator', 'trademark-search'
    ]
    
    # Get tool settings from database
    tool_settings = ToolSetting.query.all()
    
    # Get tool usage statistics
    tool_usage_stats = {}
    for tool in tools_list:
        count = ToolUsage.query.filter_by(tool_name=tool).count()
        tool_usage_stats[tool] = count
    
    # Current settings for generation limits etc.
    settings = {
        'title_generation_count': 5,
        'subtitle_generation_count': 3,
        'author_generation_count': 10,
        'keyword_research_count': 20,
        'daily_usage_limit_free': 3,
        'api_timeout_seconds': 30,
        'enable_ai_enhancement': True,
        'enable_analytics': True,
        'enable_rate_limiting': True,
    }
    
    return render_template('admin/tools.html',
                         tools_list=tools_list,
                         tool_settings=tool_settings,
                         tool_usage_stats=tool_usage_stats,
                         tool_prompts={},
                         settings=settings)

@admin_bp.route('/settings')
@login_required
@admin_required
def site_settings():
    """Site configuration and settings page"""
    
    # Organize settings by category
    settings = {
        'general': [],
        'tools': [],
        'limits': [],
        'prompts': []
    }
    
    return render_template('admin/settings.html', settings=settings)

@admin_bp.route('/user/<int:user_id>/action', methods=['POST'])
@login_required
@admin_required
def user_action(user_id):
    """Handle user management actions"""
    user = User.query.get_or_404(user_id)
    action = request.form.get('action')
    
    try:
        if action == 'upgrade':
            plan_type = request.form.get('plan_type', 'monthly')
            user.subscription_type = plan_type
            user.subscription_end = datetime.utcnow() + timedelta(days=30 if plan_type == 'monthly' else 365)
            user.daily_usage_count = 0
            
            log_action(current_user.id, 'admin_user_upgrade', 
                      f'Upgraded user {user.email} to {plan_type}', 
                      request.remote_addr, str(request.user_agent))
            
        elif action == 'disable':
            user.is_active = False
            log_action(current_user.id, 'admin_user_disable', 
                      f'Disabled user {user.email}', 
                      request.remote_addr, str(request.user_agent))
            
        elif action == 'enable':
            user.is_active = True
            log_action(current_user.id, 'admin_user_enable', 
                      f'Enabled user {user.email}', 
                      request.remote_addr, str(request.user_agent))
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/tools/toggle/<tool_name>', methods=['POST'])
@login_required
@admin_required
def toggle_tool(tool_name):
    """Enable or disable a specific tool"""
    try:
        tool_setting = ToolSetting.query.filter_by(tool_name=tool_name).first()
        
        if not tool_setting:
            tool_setting = ToolSetting(tool_name=tool_name, is_enabled=False)
            db.session.add(tool_setting)
        
        tool_setting.is_enabled = not tool_setting.is_enabled
        db.session.commit()
        
        status = 'enabled' if tool_setting.is_enabled else 'disabled'
        log_action(current_user.id, 'admin_tool_toggle', 
                  f'{status.title()} tool: {tool_name}', 
                  request.remote_addr, str(request.user_agent))
        
        return jsonify({
            'success': True, 
            'message': f'Tool {tool_name} {status} successfully',
            'enabled': tool_setting.is_enabled
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """Comprehensive analytics and reporting dashboard"""
    from datetime import datetime, timedelta
    import json
    import random
    
    # Basic metrics
    total_users = User.query.count()
    premium_users = User.query.filter_by(subscription_type='premium').count()
    total_usage = ToolUsage.query.count()
    new_users_today = User.query.filter(db.func.date(User.created_at) == datetime.utcnow().date()).count()
    usage_today = ToolUsage.query.filter(db.func.date(ToolUsage.timestamp) == datetime.utcnow().date()).count()
    
    # Revenue calculations
    total_revenue = premium_users * 15  # $15/month
    revenue_this_month = total_revenue  # Simplified for now
    premium_percentage = round((premium_users / total_users * 100) if total_users > 0 else 0, 1)
    
    # Content Management System data
    total_content_items = 45  # Placeholder
    published_content = 38
    draft_content = 7
    content_views = 12543
    
    recent_content = [
        {'title': 'KDP Guide: Book Publishing Tips', 'author': 'Admin', 'status': 'published', 'modified_date': '2025-07-20', 'views': 234},
        {'title': 'Tool Usage Tutorial', 'author': 'Admin', 'status': 'draft', 'modified_date': '2025-07-19', 'views': 0},
        {'title': 'Premium Features Overview', 'author': 'Admin', 'status': 'published', 'modified_date': '2025-07-18', 'views': 156}
    ]
    
    # Removed sections: System Logs, Error Logs, Login Activity, Performance Metrics
    
    # Chart data
    usage_trends_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    usage_trends_data = [120, 150, 180, 140, 200, 250, 190]
    
    top_tools_labels = ['Title Generator', 'Description', 'Keyword Research', 'Author Names', 'Royalty Calc']
    top_tools_data = [35, 25, 20, 12, 8]
    
    activity_labels = ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00']
    activity_data = [5, 2, 15, 35, 28, 12]
    
    revenue_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    revenue_data = [450, 680, 920, 1150, 1380, 1500]
    
    log_action(current_user.id, 'admin_analytics_access', 'Accessed analytics dashboard',
               request.remote_addr, str(request.user_agent))
    
    return render_template('admin/analytics.html',
                         # Basic metrics
                         total_users=total_users,
                         premium_users=premium_users,
                         total_usage=total_usage,
                         new_users_today=new_users_today,
                         usage_today=usage_today,
                         total_revenue=total_revenue,
                         revenue_this_month=revenue_this_month,
                         premium_percentage=premium_percentage,
                         
                         # Content Management
                         total_content_items=total_content_items,
                         published_content=published_content,
                         draft_content=draft_content,
                         content_views=content_views,
                         recent_content=recent_content,
                         
                         # Removed sections data
                         
                         # Chart data
                         usage_trends_labels=json.dumps(usage_trends_labels),
                         usage_trends_data=json.dumps(usage_trends_data),
                         top_tools_labels=json.dumps(top_tools_labels),
                         top_tools_data=json.dumps(top_tools_data),
                         activity_labels=json.dumps(activity_labels),
                         activity_data=json.dumps(activity_data),
                         revenue_labels=json.dumps(revenue_labels),
                         revenue_data=json.dumps(revenue_data))


@admin_bp.route('/website-config')
@login_required
@admin_required
def website_config_page():
    """Website configuration page"""
    # Get existing website configuration or create default
    website_config = WebsiteConfiguration.query.first()
    if not website_config:
        website_config = WebsiteConfiguration.create_default(current_user.id)
    
    # Get general stats for base template
    stats_obj = AdminStats()
    stats_obj.unread_messages = ContactMessage.query.filter_by(is_responded=False).count()
    
    log_action(current_user.id, 'admin_website_config_access', 'Accessed website configuration',
               request.remote_addr, str(request.user_agent))
    
    return render_template('admin/website_config.html', 
                         website_config=website_config,
                         general_stats=stats_obj)


@admin_bp.route('/website-config/save', methods=['POST'])
@login_required
@admin_required
def save_website_config():
    """Save website configuration settings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'})
        
        # Get existing configuration or create default
        website_config = WebsiteConfiguration.query.first()
        if not website_config:
            website_config = WebsiteConfiguration.create_default(current_user.id)
        
        # Update general settings
        if 'site_name' in data:
            website_config.site_name = data['site_name']
        if 'tagline' in data:
            website_config.tagline = data['tagline']
        if 'description' in data:
            website_config.description = data['description']
        if 'keywords' in data:
            website_config.keywords = data['keywords']
            
        # Update branding settings
        if 'logo_url' in data:
            website_config.logo_url = data['logo_url']
        if 'favicon_url' in data:
            website_config.favicon_url = data['favicon_url']
            
        # Update features settings
        if 'enable_user_registration' in data:
            website_config.enable_user_registration = data['enable_user_registration']
        if 'enable_google_auth' in data:
            website_config.enable_google_auth = data['enable_google_auth']

        if 'enable_login' in data:
            website_config.enable_login = data['enable_login']
            
        # Update content settings
        content_fields = ['hero_title', 'hero_subtitle', 'hero_free_text', 'hero_no_card_text', 
                         'features_title', 'features_subtitle', 'pricing_title', 'pricing_subtitle',
                         'cta_title', 'cta_subtitle', 'footer_description', 'footer_tagline']
        for field in content_fields:
            if field in data:
                setattr(website_config, field, data[field])
        
        # Update pricing plan settings
        pricing_fields = ['free_plan_name', 'free_plan_price', 'free_plan_period',
                         'free_plan_feature1', 'free_plan_feature2', 'free_plan_feature3', 'free_plan_feature4', 'free_plan_feature5',
                         'free_plan_feature6', 'free_plan_feature7', 'free_plan_feature8',
                         'free_plan_button_text', 'free_plan_current_button_text',
                         'pro_plan_name', 'pro_plan_price', 'pro_plan_period',
                         'pro_plan_feature1', 'pro_plan_feature2', 'pro_plan_feature3', 'pro_plan_feature4', 'pro_plan_feature5',
                         'pro_plan_feature6', 'pro_plan_feature7', 'pro_plan_feature8',
                         'pro_plan_button_text', 'pro_plan_current_button_text']
        for field in pricing_fields:
            if field in data:
                setattr(website_config, field, data[field])
        
        # Update tools content settings
        tools_fields = ['tool_title_generator_title', 'tool_title_generator_description', 'tool_title_generator_icon',
                       'tool_description_generator_title', 'tool_description_generator_description', 'tool_description_generator_icon',
                       'tool_keyword_research_title', 'tool_keyword_research_description', 'tool_keyword_research_icon',
                       'tool_royalty_calculator_title', 'tool_royalty_calculator_description', 'tool_royalty_calculator_icon',
                       'tool_subtitle_generator_title', 'tool_subtitle_generator_description', 'tool_subtitle_generator_icon',
                       'tool_author_generator_title', 'tool_author_generator_description', 'tool_author_generator_icon',
                       'tool_category_finder_title', 'tool_category_finder_description', 'tool_category_finder_icon',
                       'tool_trademark_search_title', 'tool_trademark_search_description', 'tool_trademark_search_icon']
        for field in tools_fields:
            if field in data:
                setattr(website_config, field, data[field])
        
        # Update navigation and footer settings
        nav_footer_fields = ['pricing_guarantee_text', 'nav_home_text', 'nav_dashboard_text', 'nav_plans_text', 'nav_contact_text',
                            'footer_quick_links_title', 'footer_quick_links_1', 'footer_quick_links_2', 'footer_quick_links_3',
                            'footer_tools_title', 'footer_tools_1', 'footer_tools_2', 'footer_tools_3', 'footer_tools_4',
                            'footer_copyright_text']
        for field in nav_footer_fields:
            if field in data:
                setattr(website_config, field, data[field])
        
        # Update button text settings
        button_fields = ['button_start_free_trial', 'button_sign_in', 'button_login', 'button_register', 'button_logout', 'button_get_started', 'button_view_pricing', 'button_start_free_today']
        for field in button_fields:
            if field in data:
                setattr(website_config, field, data[field])
        if 'free_daily_limit' in data:
            website_config.free_daily_limit = int(data['free_daily_limit'])
        if 'premium_daily_limit' in data:
            website_config.premium_daily_limit = int(data['premium_daily_limit'])
            
        # Update SEO settings
        if 'google_analytics_id' in data:
            website_config.google_analytics_id = data['google_analytics_id']
        if 'google_tag_manager_id' in data:
            website_config.google_tag_manager_id = data['google_tag_manager_id']
        if 'facebook_pixel_id' in data:
            website_config.facebook_pixel_id = data['facebook_pixel_id']
        if 'custom_head_tags' in data:
            website_config.custom_head_tags = data['custom_head_tags']
            
        # Update contact settings
        if 'contact_email' in data:
            website_config.contact_email = data['contact_email']
        if 'contact_phone' in data:
            website_config.contact_phone = data['contact_phone']
        if 'contact_address' in data:
            website_config.contact_address = data['contact_address']
        if 'facebook_url' in data:
            website_config.facebook_url = data['facebook_url']
        if 'twitter_url' in data:
            website_config.twitter_url = data['twitter_url']
        if 'instagram_url' in data:
            website_config.instagram_url = data['instagram_url']
        if 'linkedin_url' in data:
            website_config.linkedin_url = data['linkedin_url']
            
        # Update maintenance settings
        if 'enable_maintenance' in data:
            website_config.enable_maintenance = bool(data['enable_maintenance'])
        if 'maintenance_title' in data:
            website_config.maintenance_title = data['maintenance_title']
        if 'maintenance_message' in data:
            website_config.maintenance_message = data['maintenance_message']
        if 'maintenance_estimated_time' in data:
            website_config.maintenance_estimated_time = data['maintenance_estimated_time']
        if 'maintenance_contact_info' in data:
            website_config.maintenance_contact_info = data['maintenance_contact_info']
            
        # Update timestamps
        website_config.updated_at = datetime.utcnow()
        website_config.updated_by = current_user.id
        
        db.session.commit()
        
        log_action(current_user.id, 'admin_website_config_save', 'Updated website configuration',
                   request.remote_addr, str(request.user_agent))
        
        return jsonify({'success': True, 'message': 'Website configuration saved successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to save configuration: {str(e)}'})


@admin_bp.route('/website-config/reset', methods=['POST'])
@login_required
@admin_required
def reset_website_config():
    """Reset website configuration to defaults"""
    try:
        website_config = WebsiteConfiguration.query.first()
        if website_config:
            db.session.delete(website_config)
        
        # Create new default configuration
        default_config = WebsiteConfiguration.create_default(current_user.id)
        db.session.commit()
        
        log_action(current_user.id, 'admin_website_config_reset', 'Reset website configuration to defaults',
                   request.remote_addr, str(request.user_agent))
        
        return jsonify({'success': True, 'message': 'Website configuration reset to defaults'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@admin_bp.route('/tools-config')
@login_required
@admin_required
def tools_config_page():
    """Tools configuration page"""
    # Get all tool configurations
    tools = ToolConfiguration.query.order_by(ToolConfiguration.sort_order).all()
    
    # Get maintenance mode information
    maintenance_info = MaintenanceMode.get_current_info()
    
    return render_template('admin/tools_config.html', 
                         tools=tools, 
                         maintenance_info=maintenance_info)

@admin_bp.route('/tools-management')
@login_required
@admin_required
def tools_management_page():
    """Tools management page with advanced controls"""
    from datetime import datetime, timedelta
    
    # Get all tools with usage statistics
    tools = ToolConfiguration.query.order_by(ToolConfiguration.sort_order).all()
    
    # Calculate usage statistics for each tool
    today = datetime.utcnow().date()
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    for tool in tools:
        # Get usage counts
        total_usage = ToolUsage.query.filter_by(tool_name=tool.tool_name).count()
        daily_usage = ToolUsage.query.filter(
            ToolUsage.tool_name == tool.tool_name,
            db.func.date(ToolUsage.timestamp) == today
        ).count()
        weekly_usage = ToolUsage.query.filter(
            ToolUsage.tool_name == tool.tool_name,
            ToolUsage.timestamp >= week_ago
        ).count()
        
        # Get usage by subscription type
        free_usage = ToolUsage.query.join(User).filter(
            ToolUsage.tool_name == tool.tool_name,
            User.subscription_type == 'free'
        ).count()
        premium_usage = ToolUsage.query.join(User).filter(
            ToolUsage.tool_name == tool.tool_name,
            User.subscription_type.in_(['monthly', 'yearly'])
        ).count()
        
        # Add statistics to tool object
        tool.usage_count = total_usage
        tool.daily_usage = daily_usage
        tool.weekly_usage = weekly_usage
        tool.free_usage = free_usage
        tool.premium_usage = premium_usage
    
    # Calculate max usage for chart scaling
    max_usage = max([tool.usage_count for tool in tools]) if tools else 1
    
    return render_template('admin/tools_management.html', 
                         tools=tools, 
                         max_usage=max_usage)

@admin_bp.route('/tools/update-status', methods=['POST'])
@login_required
@admin_required
def update_tool_status():
    """Update tool enabled/disabled status"""
    try:
        data = request.get_json()
        tool_id = data.get('tool_id')
        is_enabled = data.get('is_enabled', True)
        
        tool = ToolConfiguration.query.get_or_404(tool_id)
        tool.is_enabled = is_enabled
        
        db.session.commit()
        
        log_action(current_user.id, 'admin_tool_status_update', 
                  f'{"Enabled" if is_enabled else "Disabled"} tool {tool.tool_name}',
                  request.remote_addr, str(request.user_agent))
        
        return jsonify({
            'success': True,
            'message': f'Tool {"enabled" if is_enabled else "disabled"} successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error updating tool status: {str(e)}'})

@admin_bp.route('/tools/update-access', methods=['POST'])
@login_required
@admin_required
def update_tool_access():
    """Update tool access control (free/premium/disabled)"""
    try:
        data = request.get_json()
        tool_id = data.get('tool_id')
        requires_paid_plan = data.get('requires_paid_plan', False)
        is_enabled = data.get('is_enabled', True)
        
        tool = ToolConfiguration.query.get_or_404(tool_id)
        tool.requires_paid_plan = requires_paid_plan
        tool.is_enabled = is_enabled
        
        db.session.commit()
        
        access_type = 'disabled' if not is_enabled else ('premium' if requires_paid_plan else 'free')
        
        log_action(current_user.id, 'admin_tool_access_update', 
                  f'Updated tool {tool.tool_name} access to {access_type}',
                  request.remote_addr, str(request.user_agent))
        
        return jsonify({
            'success': True,
            'message': f'Tool access updated to {access_type}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error updating tool access: {str(e)}'})

@admin_bp.route('/tools/update-order', methods=['POST'])
@login_required
@admin_required
def update_tools_order():
    """Update tools display order"""
    try:
        data = request.get_json()
        order = data.get('order', [])
        
        for item in order:
            tool_id = item.get('tool_id')
            sort_order = item.get('sort_order')
            
            tool = ToolConfiguration.query.get(tool_id)
            if tool:
                tool.sort_order = sort_order
        
        db.session.commit()
        
        log_action(current_user.id, 'admin_tools_reorder', 
                  f'Updated tools display order',
                  request.remote_addr, str(request.user_agent))
        
        return jsonify({
            'success': True,
            'message': 'Tools order updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error updating tools order: {str(e)}'})

@admin_bp.route('/tools/bulk-action', methods=['POST'])
@login_required
@admin_required
def tools_bulk_action():
    """Perform bulk actions on all tools"""
    try:
        data = request.get_json()
        action = data.get('action')
        
        tools = ToolConfiguration.query.all()
        
        for tool in tools:
            if action == 'enable':
                tool.is_enabled = True
            elif action == 'disable':
                tool.is_enabled = False
            elif action == 'free':
                tool.requires_paid_plan = False
                tool.is_enabled = True
            elif action == 'premium':
                tool.requires_paid_plan = True
                tool.is_enabled = True
        
        db.session.commit()
        
        log_action(current_user.id, 'admin_tools_bulk_action', 
                  f'Performed bulk action: {action} on all tools',
                  request.remote_addr, str(request.user_agent))
        
        return jsonify({
            'success': True,
            'message': f'Bulk action "{action}" completed successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error performing bulk action: {str(e)}'})

@admin_bp.route('/tools/reset-defaults', methods=['POST'])
@login_required
@admin_required
def reset_tools_defaults():
    """Reset all tools to default settings"""
    try:
        # Default tools configuration
        default_tools = [
            {'tool_name': 'title_generator', 'display_name': 'Title Generator', 'is_enabled': True, 'requires_paid_plan': False, 'sort_order': 1, 'icon': 'fas fa-magic'},
            {'tool_name': 'subtitle_generator', 'display_name': 'Subtitle Generator', 'is_enabled': True, 'requires_paid_plan': False, 'sort_order': 2, 'icon': 'fas fa-heading'},
            {'tool_name': 'description_generator', 'display_name': 'Description Generator', 'is_enabled': True, 'requires_paid_plan': False, 'sort_order': 3, 'icon': 'fas fa-file-alt'},
            {'tool_name': 'author_generator', 'display_name': 'Author Generator', 'is_enabled': True, 'requires_paid_plan': False, 'sort_order': 4, 'icon': 'fas fa-user-edit'},
            {'tool_name': 'keyword_research', 'display_name': 'Keyword Research', 'is_enabled': True, 'requires_paid_plan': True, 'sort_order': 5, 'icon': 'fas fa-search'},
            {'tool_name': 'category_finder', 'display_name': 'Category Finder', 'is_enabled': True, 'requires_paid_plan': True, 'sort_order': 6, 'icon': 'fas fa-tags'},
            {'tool_name': 'royalty_calculator', 'display_name': 'Royalty Calculator', 'is_enabled': True, 'requires_paid_plan': False, 'sort_order': 7, 'icon': 'fas fa-calculator'},
            {'tool_name': 'trademark_search', 'display_name': 'Trademark Search', 'is_enabled': True, 'requires_paid_plan': True, 'sort_order': 8, 'icon': 'fas fa-shield-alt'}
        ]
        
        # Delete existing configurations
        ToolConfiguration.query.delete()
        
        # Create new default configurations
        for tool_data in default_tools:
            tool = ToolConfiguration(**tool_data)
            db.session.add(tool)
        
        db.session.commit()
        
        log_action(current_user.id, 'admin_tools_reset_defaults', 
                  'Reset all tools to default configuration',
                  request.remote_addr, str(request.user_agent))
        
        return jsonify({
            'success': True,
            'message': 'Tools reset to defaults successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error resetting tools: {str(e)}'})

@admin_bp.route('/tools/data')
@login_required
@admin_required
def get_tools_data():
    """Get tools statistics data"""
    try:
        tools = ToolConfiguration.query.all()
        
        stats = {
            'total_tools': len(tools),
            'active_tools': len([t for t in tools if t.is_enabled]),
            'disabled_tools': len([t for t in tools if not t.is_enabled]),
            'premium_tools': len([t for t in tools if t.requires_paid_plan])
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting tools data: {str(e)}'})

@admin_bp.route('/user/<int:user_id>/tools/restrict', methods=['POST'])
@login_required
@admin_required
def restrict_user_tools(user_id):
    """Restrict specific tools for a user"""
    try:
        data = request.get_json()
        tool_names = data.get('tools', [])
        action = data.get('action', 'restrict')  # 'restrict' or 'unrestrict'
        
        user = User.query.get_or_404(user_id)
        
        if action == 'restrict':
            # Add restrictions
            for tool_name in tool_names:
                existing = UserToolRestriction.query.filter_by(
                    user_id=user_id, 
                    tool_name=tool_name
                ).first()
                
                if not existing:
                    restriction = UserToolRestriction(
                        user_id=user_id,
                        tool_name=tool_name,
                        is_disabled=True
                    )
                    db.session.add(restriction)
                else:
                    existing.is_disabled = True
        
        elif action == 'unrestrict':
            # Remove restrictions
            UserToolRestriction.query.filter(
                UserToolRestriction.user_id == user_id,
                UserToolRestriction.tool_name.in_(tool_names)
            ).delete(synchronize_session=False)
        
        db.session.commit()
        
        log_action(current_user.id, 'admin_tool_restriction', 
                  f'{action.title()}ed tools {tool_names} for user {user.email}', 
                  request.remote_addr, str(request.user_agent))
        
        return jsonify({
            'success': True,
            'message': f'Tools {action}ed successfully for user {user.email}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error restricting tools: {str(e)}'})

@admin_bp.route('/user/<int:user_id>/tools/status')
@login_required
@admin_required
def get_user_tool_restrictions(user_id):
    """Get user's tool restrictions"""
    try:
        user = User.query.get_or_404(user_id)
        restrictions = UserToolRestriction.query.filter_by(user_id=user_id).all()
        
        restricted_tools = [r.tool_name for r in restrictions if r.is_disabled]
        
        all_tools = [
            'title_generator', 'subtitle_generator', 'description_generator',
            'author_generator', 'keyword_research', 'category_finder',
            'royalty_calculator', 'trademark_search'
        ]
        
        tool_status = {}
        for tool in all_tools:
            tool_status[tool] = {
                'name': tool.replace('_', ' ').title(),
                'restricted': tool in restricted_tools,
                'enabled': tool not in restricted_tools
            }
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'name': f"{user.first_name} {user.last_name}"
            },
            'tools': tool_status
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting tool status: {str(e)}'})

@admin_bp.route('/system/status')
@login_required
@admin_required
def get_system_status():
    """Get current system status including maintenance mode"""
    try:
        maintenance_setting = ToolSetting.query.filter_by(tool_name='maintenance_mode').first()
        maintenance_enabled = maintenance_setting.setting_value == 'true' if maintenance_setting else False
        
        # Get tool status
        tool_settings = ToolSetting.query.all()
        tools_status = {}
        
        all_tools = [
            'title_generator', 'subtitle_generator', 'description_generator',
            'author_generator', 'keyword_research', 'category_finder',
            'royalty_calculator', 'trademark_search'
        ]
        
        for tool in all_tools:
            setting = next((s for s in tool_settings if s.tool_name == tool), None)
            tools_status[tool] = {
                'enabled': setting.is_enabled if setting else True,
                'requires_paid': setting.requires_paid_plan if setting else False
            }
        
        return jsonify({
            'success': True,
            'maintenance_mode': maintenance_enabled,
            'tools': tools_status,
            'system_health': 'operational'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting system status: {str(e)}'})

@admin_bp.route('/system-logs')
@login_required
@admin_required
def system_logs():
    """System logs and activity monitoring"""
    log_type = request.args.get('type', 'all')
    page = request.args.get('page', 1, type=int)
    
    query = ActionLog.query
    
    if log_type != 'all':
        query = query.filter(ActionLog.action.contains(log_type))
    
    logs = query.order_by(ActionLog.timestamp.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    return render_template('admin/system_logs.html', logs=logs, log_type=log_type)

@admin_bp.route('/user/<int:user_id>')
@login_required
@admin_required
def user_details(user_id):
    """Individual user details page"""
    user = User.query.get_or_404(user_id)
    
    tool_usage = ToolUsage.query.filter_by(user_id=user_id).order_by(ToolUsage.timestamp.desc()).limit(20).all()
    activities = ActionLog.query.filter_by(user_id=user_id).order_by(ActionLog.timestamp.desc()).limit(10).all()
    restrictions = UserToolRestriction.query.filter_by(user_id=user_id).all()
    
    return render_template('admin/user_details.html', 
                         user=user, 
                         tool_usage=tool_usage,
                         activities=activities,
                         restrictions=restrictions)



@admin_bp.route('/contact-messages')
@login_required
@admin_required
def contact_messages():
    """Contact messages management"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = ContactMessage.query
    
    if status_filter == 'unread':
        query = query.filter_by(is_responded=False)
    elif status_filter == 'read':
        query = query.filter_by(is_responded=True)
    
    messages = query.order_by(ContactMessage.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/contact_messages.html', messages=messages, status_filter=status_filter)

@admin_bp.route('/backup')
@login_required
@admin_required
def backup():
    """System backup page"""
    return render_template('admin/backup.html')

@admin_bp.route('/monitoring')
@login_required
@admin_required
def monitoring():
    """System monitoring page"""
    # Get active users count (users with recent activity)
    recent_activity = datetime.utcnow() - timedelta(hours=1)
    active_users = User.query.filter(User.last_login_at >= recent_activity).count() if User.query.filter(User.last_login_at.isnot(None)).first() else 0
    
    return render_template('admin/monitoring.html', active_users=active_users)

@admin_bp.route('/database')
@login_required
@admin_required
def database():
    """Database management page"""
    # Database statistics
    total_users = User.query.count()
    total_usage = ToolUsage.query.count()
    table_count = 12  # Known table count
    
    return render_template('admin/database.html', 
                         total_users=total_users,
                         total_usage=total_usage,
                         table_count=table_count)

# Add admin action routes for user management
@admin_bp.route('/user/<int:user_id>/activate', methods=['POST'])
@login_required
@admin_required
def activate_user(user_id):
    """Activate a user account"""
    try:
        user = User.query.get_or_404(user_id)
        user.is_active = True
        db.session.commit()
        
        log_action(current_user.id, 'admin_activate_user', 
                  f'Activated user {user.email}', 
                  request.remote_addr, str(request.user_agent))
        
        return jsonify({'success': True, 'message': 'User activated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/user/<int:user_id>/deactivate', methods=['POST'])
@login_required
@admin_required
def deactivate_user(user_id):
    """Deactivate a user account"""
    try:
        user = User.query.get_or_404(user_id)
        user.is_active = False
        db.session.commit()
        
        log_action(current_user.id, 'admin_deactivate_user', 
                  f'Deactivated user {user.email}', 
                  request.remote_addr, str(request.user_agent))
        
        return jsonify({'success': True, 'message': 'User deactivated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/user/<int:user_id>/make-admin', methods=['POST'])
@login_required
@admin_required
def make_admin(user_id):
    """Make a user an admin"""
    try:
        user = User.query.get_or_404(user_id)
        user.is_admin = True
        db.session.commit()
        
        log_action(current_user.id, 'admin_promote_user', 
                  f'Promoted user {user.email} to admin', 
                  request.remote_addr, str(request.user_agent))
        
        return jsonify({'success': True, 'message': 'User promoted to admin successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/user/<int:user_id>/remove-admin', methods=['POST'])
@login_required
@admin_required
def remove_admin(user_id):
    """Remove admin privileges from a user"""
    try:
        user = User.query.get_or_404(user_id)
        user.is_admin = False
        db.session.commit()
        
        log_action(current_user.id, 'admin_demote_user', 
                  f'Removed admin privileges from {user.email}', 
                  request.remote_addr, str(request.user_agent))
        
        return jsonify({'success': True, 'message': 'Admin privileges removed successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user account"""
    try:
        user = User.query.get_or_404(user_id)
        user_email = user.email
        db.session.delete(user)
        db.session.commit()
        
        log_action(current_user.id, 'admin_delete_user', 
                  f'Deleted user {user_email}', 
                  request.remote_addr, str(request.user_agent))
        
        return jsonify({'success': True, 'message': 'User deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/message/<int:message_id>/respond', methods=['POST'])
@login_required
@admin_required
def respond_to_message(message_id):
    """Mark a contact message as responded"""
    try:
        message = ContactMessage.query.get_or_404(message_id)
        message.is_responded = True
        message.responded_at = datetime.utcnow()
        message.responded_by = current_user.id
        db.session.commit()
        
        log_action(current_user.id, 'admin_respond_message', 
                  f'Responded to message from {message.email}', 
                  request.remote_addr, str(request.user_agent))
        
        return jsonify({'success': True, 'message': 'Message marked as responded'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/message/<int:message_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_message(message_id):
    """Delete a contact message"""
    try:
        message = ContactMessage.query.get_or_404(message_id)
        db.session.delete(message)
        db.session.commit()
        
        log_action(current_user.id, 'admin_delete_message', 
                  f'Deleted message from {message.email}', 
                  request.remote_addr, str(request.user_agent))
        
        return jsonify({'success': True, 'message': 'Message deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


# API Settings Routes
@admin_bp.route('/api-settings')
@login_required
@admin_required
def api_settings():
    """API Keys management page"""
    # Get API configurations
    api_configs = {
        'openai_api_key': SiteConfiguration.get_config('openai_api_key', ''),
        'groq_api_key': SiteConfiguration.get_config('groq_api_key', ''),
        'google_oauth_client_id': SiteConfiguration.get_config('google_oauth_client_id', ''),
        'google_oauth_client_secret': SiteConfiguration.get_config('google_oauth_client_secret', ''),
        'sendgrid_api_key': SiteConfiguration.get_config('sendgrid_api_key', ''),
        'trademark_api_key': SiteConfiguration.get_config('trademark_api_key', ''),
        'trademark_api_url': SiteConfiguration.get_config('trademark_api_url', '')
    }
    
    # Get general stats for base template  
    stats_obj = AdminStats()
    stats_obj.unread_messages = ContactMessage.query.filter_by(is_responded=False).count()
    
    return render_template('admin/api_settings.html', api_configs=api_configs, general_stats=stats_obj)


@admin_bp.route('/api-settings/save', methods=['POST'])
@login_required
@admin_required
def save_api_settings():
    """Save API settings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'})
        
        # API key fields to save
        api_fields = [
            'openai_api_key', 'groq_api_key', 'google_oauth_client_id',
            'google_oauth_client_secret', 'sendgrid_api_key', 'trademark_api_key',
            'trademark_api_url'
        ]
        
        for field in api_fields:
            if field in data and data[field]:
                SiteConfiguration.set_config(
                    key=field,
                    value=data[field],
                    category='api',
                    user_id=current_user.id
                )
        
        log_action(current_user.id, 'admin_api_settings_save', 'Updated API settings',
                   request.remote_addr, str(request.user_agent))
        
        return jsonify({'success': True, 'message': 'API settings saved successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to save API settings: {str(e)}'})


# Stripe Settings Routes
@admin_bp.route('/stripe-settings')
@login_required
@admin_required
def stripe_settings():
    """Stripe payment settings page"""
    stripe_configs = {
        'stripe_secret_key': SiteConfiguration.get_config('stripe_secret_key', ''),
        'stripe_publishable_key': SiteConfiguration.get_config('stripe_publishable_key', ''),
        'stripe_webhook_secret': SiteConfiguration.get_config('stripe_webhook_secret', ''),
        'stripe_test_mode': SiteConfiguration.get_config('stripe_test_mode', 'true'),
        'stripe_monthly_price_id': SiteConfiguration.get_config('stripe_monthly_price_id', ''),
        'stripe_yearly_price_id': SiteConfiguration.get_config('stripe_yearly_price_id', '')
    }
    
    # Get general stats for base template
    stats_obj = AdminStats()
    stats_obj.unread_messages = ContactMessage.query.filter_by(is_responded=False).count()
    
    return render_template('admin/stripe_settings.html', stripe_configs=stripe_configs, general_stats=stats_obj)


@admin_bp.route('/stripe-settings/save', methods=['POST'])
@login_required
@admin_required
def save_stripe_settings():
    """Save Stripe settings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'})
        
        stripe_fields = [
            'stripe_secret_key', 'stripe_publishable_key', 'stripe_webhook_secret',
            'stripe_test_mode', 'stripe_monthly_price_id', 'stripe_yearly_price_id'
        ]
        
        for field in stripe_fields:
            if field in data:
                SiteConfiguration.set_config(
                    key=field,
                    value=data[field],
                    category='payment',
                    user_id=current_user.id
                )
        
        log_action(current_user.id, 'admin_stripe_settings_save', 'Updated Stripe settings',
                   request.remote_addr, str(request.user_agent))
        
        return jsonify({'success': True, 'message': 'Stripe settings saved successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to save Stripe settings: {str(e)}'})


# Subscription Management Routes
@admin_bp.route('/subscription-management')
@login_required
@admin_required
def subscription_management():
    """Subscription management page"""
    # Get subscription statistics
    total_users = User.query.count()
    free_users = User.query.filter_by(subscription_type='free').count()
    monthly_users = User.query.filter_by(subscription_type='monthly').count()
    yearly_users = User.query.filter_by(subscription_type='yearly').count()
    
    # Get recent subscriptions
    recent_subscriptions = User.query.filter(
        User.subscription_type.in_(['monthly', 'yearly'])
    ).order_by(User.subscription_start.desc()).limit(20).all()
    
    # Get expiring subscriptions (next 7 days)
    week_from_now = datetime.utcnow() + timedelta(days=7)
    expiring_soon = User.query.filter(
        User.subscription_end <= week_from_now,
        User.subscription_type.in_(['monthly', 'yearly'])
    ).all()
    
    subscription_stats = {
        'total_users': total_users,
        'free_users': free_users,
        'monthly_users': monthly_users,
        'yearly_users': yearly_users,
        'recent_subscriptions': recent_subscriptions,
        'expiring_soon': expiring_soon
    }
    
    # Get general stats for base template
    stats_obj = AdminStats()
    stats_obj.unread_messages = ContactMessage.query.filter_by(is_responded=False).count()
    
    return render_template('admin/subscription_management.html', 
                         stats=subscription_stats, 
                         general_stats=stats_obj)


@admin_bp.route('/subscription-management/cancel/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def cancel_user_subscription(user_id):
    """Cancel user subscription"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Cancel subscription
        user.subscription_type = 'free'
        user.subscription_end = None
        user.stripe_subscription_id = None
        user.daily_usage_count = 0
        
        db.session.commit()
        
        log_action(current_user.id, 'admin_subscription_cancel', 
                   f'Cancelled subscription for user {user.email}',
                   request.remote_addr, str(request.user_agent))
        
        return jsonify({'success': True, 'message': 'Subscription cancelled successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to cancel subscription: {str(e)}'})


# Revenue Analytics Routes
@admin_bp.route('/revenue-analytics')
@login_required
@admin_required
def revenue_analytics():
    """Revenue analytics page"""
    # Monthly revenue calculation
    monthly_users = User.query.filter_by(subscription_type='monthly').count()
    yearly_users = User.query.filter_by(subscription_type='yearly').count()
    
    monthly_revenue = monthly_users * 15  # $15/month
    yearly_revenue = yearly_users * 150  # $150/year (annual)
    total_mrr = monthly_revenue + (yearly_revenue / 12)  # Monthly Recurring Revenue
    
    # Revenue by month (last 12 months)
    revenue_by_month = []
    for i in range(12):
        month_date = datetime.utcnow() - timedelta(days=30*i)
        month_users = User.query.filter(
            User.subscription_start <= month_date,
            User.subscription_type.in_(['monthly', 'yearly'])
        ).count()
        revenue_by_month.append({
            'month': month_date.strftime('%Y-%m'),
            'revenue': month_users * 15  # Simplified calculation
        })
    
    analytics = {
        'monthly_users': monthly_users,
        'yearly_users': yearly_users,
        'monthly_revenue': monthly_revenue,
        'yearly_revenue': yearly_revenue,
        'total_mrr': total_mrr,
        'revenue_by_month': revenue_by_month
    }
    
    # Get general stats for base template
    stats_obj = AdminStats()
    stats_obj.unread_messages = ContactMessage.query.filter_by(is_responded=False).count()
    
    return render_template('admin/revenue_analytics.html', analytics=analytics, general_stats=stats_obj)


# Pricing Settings Routes
@admin_bp.route('/pricing-settings')
@login_required
@admin_required
def pricing_settings():
    """Pricing settings page"""
    pricing_configs = {
        'monthly_price': SiteConfiguration.get_config('monthly_price', '15'),
        'yearly_price': SiteConfiguration.get_config('yearly_price', '150'),
        'free_daily_limit': SiteConfiguration.get_config('free_daily_limit', '3'),
        'premium_daily_limit': SiteConfiguration.get_config('premium_daily_limit', '999'),
        'trial_days': SiteConfiguration.get_config('trial_days', '0'),
        'currency': SiteConfiguration.get_config('currency', 'USD')
    }
    
    # Get general stats for base template
    stats_obj = AdminStats()
    stats_obj.unread_messages = ContactMessage.query.filter_by(is_responded=False).count()
    
    return render_template('admin/pricing_settings.html', pricing_configs=pricing_configs, general_stats=stats_obj)


@admin_bp.route('/pricing-settings/save', methods=['POST'])
@login_required
@admin_required
def save_pricing_settings():
    """Save pricing settings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'})
        
        pricing_fields = [
            'monthly_price', 'yearly_price', 'free_daily_limit',
            'premium_daily_limit', 'trial_days', 'currency'
        ]
        
        for field in pricing_fields:
            if field in data:
                SiteConfiguration.set_config(
                    key=field,
                    value=data[field],
                    category='pricing',
                    user_id=current_user.id
                )
        
        log_action(current_user.id, 'admin_pricing_settings_save', 'Updated pricing settings',
                   request.remote_addr, str(request.user_agent))
        
        return jsonify({'success': True, 'message': 'Pricing settings saved successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to save pricing settings: {str(e)}'})


