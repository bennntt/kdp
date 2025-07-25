from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

# Initialize db
db = SQLAlchemy()

class ToolConfiguration(db.Model):
    """Tool configuration and management"""
    __tablename__ = 'tool_configuration'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    tool_name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50), default='fas fa-tools')
    is_enabled = db.Column(db.Boolean, default=True)
    requires_paid_plan = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    daily_limit_free = db.Column(db.Integer, default=3)
    daily_limit_paid = db.Column(db.Integer, default=50)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ToolConfiguration {self.tool_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tool_name': self.tool_name,
            'display_name': self.display_name,
            'description': self.description,
            'icon': self.icon,
            'is_enabled': self.is_enabled,
            'requires_paid_plan': self.requires_paid_plan,
            'sort_order': self.sort_order,
            'daily_limit_free': self.daily_limit_free,
            'daily_limit_paid': self.daily_limit_paid
        }
    
    @staticmethod
    def get_enabled_tools():
        """Get all enabled tools ordered by sort_order"""
        return ToolConfiguration.query.filter_by(is_enabled=True).order_by(ToolConfiguration.sort_order).all()
    
    @staticmethod
    def get_tool_by_name(tool_name):
        """Get tool configuration by name"""
        return ToolConfiguration.query.filter_by(tool_name=tool_name).first()
    
    @staticmethod
    def is_tool_available_for_user(tool_name, user):
        """Check if tool is available for specific user"""
        tool = ToolConfiguration.get_tool_by_name(tool_name)
        if not tool or not tool.is_enabled:
            return False
        
        # Check if tool requires paid plan
        if tool.requires_paid_plan:
            return user.subscription_type in ['monthly', 'yearly']
        
        return True
    
    @staticmethod
    def create_default_tools():
        """Create default tool configurations"""
        default_tools = [
            {
                'tool_name': 'title_generator',
                'display_name': 'Title Generator',
                'description': 'Generate compelling book titles that grab attention and drive sales',
                'icon': 'fas fa-magic',
                'is_enabled': True,
                'requires_paid_plan': False,
                'sort_order': 1
            },
            {
                'tool_name': 'subtitle_generator',
                'display_name': 'Subtitle Generator',
                'description': 'Create perfect subtitles that complement your main title',
                'icon': 'fas fa-heading',
                'is_enabled': True,
                'requires_paid_plan': False,
                'sort_order': 2
            },
            {
                'tool_name': 'description_generator',
                'display_name': 'Description Generator',
                'description': 'Write persuasive book descriptions that convert browsers into buyers',
                'icon': 'fas fa-file-alt',
                'is_enabled': True,
                'requires_paid_plan': False,
                'sort_order': 3
            },
            {
                'tool_name': 'author_generator',
                'display_name': 'Author Generator',
                'description': 'Generate professional pen names that fit your genre and style',
                'icon': 'fas fa-user-edit',
                'is_enabled': True,
                'requires_paid_plan': False,
                'sort_order': 4
            },
            {
                'tool_name': 'keyword_research',
                'display_name': 'Keyword Research',
                'description': 'Discover high-traffic keywords to improve your book discoverability',
                'icon': 'fas fa-search',
                'is_enabled': True,
                'requires_paid_plan': True,
                'sort_order': 5
            },
            {
                'tool_name': 'category_finder',
                'display_name': 'Category Finder',
                'description': 'Find the best Amazon categories for maximum visibility',
                'icon': 'fas fa-tags',
                'is_enabled': True,
                'requires_paid_plan': True,
                'sort_order': 6
            },
            {
                'tool_name': 'royalty_calculator',
                'display_name': 'Royalty Calculator',
                'description': 'Calculate your potential earnings and optimize pricing strategy',
                'icon': 'fas fa-calculator',
                'is_enabled': True,
                'requires_paid_plan': False,
                'sort_order': 7
            },
            {
                'tool_name': 'trademark_search',
                'display_name': 'Trademark Search',
                'description': 'Check for trademark conflicts before publishing your book',
                'icon': 'fas fa-shield-alt',
                'is_enabled': True,
                'requires_paid_plan': True,
                'sort_order': 8
            }
        ]
        
        for tool_data in default_tools:
            existing_tool = ToolConfiguration.query.filter_by(tool_name=tool_data['tool_name']).first()
            if not existing_tool:
                tool = ToolConfiguration(**tool_data)
                db.session.add(tool)
        
        db.session.commit()

class MaintenanceMode(db.Model):
    """Maintenance mode configuration"""
    __tablename__ = 'maintenance_mode'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    is_enabled = db.Column(db.Boolean, default=False)
    message = db.Column(db.Text, default='Site is under maintenance')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ToolSetting(db.Model):
    """Tool settings and configuration"""
    __tablename__ = 'tool_setting'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(64))
    password_reset_token = db.Column(db.String(64))
    password_reset_expires = db.Column(db.DateTime)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Subscription fields
    subscription_type = db.Column(db.String(20), default='free')  # 'free', 'monthly', 'yearly'
    subscription_start = db.Column(db.DateTime)
    subscription_end = db.Column(db.DateTime)
    stripe_customer_id = db.Column(db.String(100))
    stripe_subscription_id = db.Column(db.String(100))
    
    # Usage tracking
    daily_usage_count = db.Column(db.Integer, default=0)
    last_usage_date = db.Column(db.Date)
    
    # Security fields
    last_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(45))
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32))
    session_token = db.Column(db.String(64))
    session_expires = db.Column(db.DateTime)
    
    # Settings fields
    theme_preference = db.Column(db.String(10), default='dark')  # 'dark', 'light', 'auto'
    language_preference = db.Column(db.String(5), default='en')  # 'en', 'ar', 'es', 'fr'
    timezone_preference = db.Column(db.String(50), default='UTC')
    compact_mode = db.Column(db.Boolean, default=False)
    animations_enabled = db.Column(db.Boolean, default=True)
    email_notifications = db.Column(db.Boolean, default=True)
    browser_notifications = db.Column(db.Boolean, default=False)
    marketing_emails = db.Column(db.Boolean, default=False)
    profile_picture = db.Column(db.String(255))
    display_name = db.Column(db.String(100))
    
    # Relationships
    tool_usage = db.relationship('ToolUsage', backref='user', lazy=True, cascade='all, delete-orphan')
    action_logs = db.relationship('ActionLog', backref='user', lazy=True, cascade='all, delete-orphan')
    admin_messages = db.relationship('AdminMessage', backref='user', lazy=True, cascade='all, delete-orphan')
    tool_restrictions = db.relationship('UserToolRestriction', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_email_verification_token(self):
        self.email_verification_token = secrets.token_urlsafe(32)
        return self.email_verification_token
    
    def generate_password_reset_token(self):
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        return self.password_reset_token
    
    def can_use_tool(self, tool_name):
        """Check if user can use a specific tool"""
        # Check if tool is restricted for this user
        restriction = UserToolRestriction.query.filter_by(
            user_id=self.id, 
            tool_name=tool_name
        ).first()
        if restriction and restriction.is_disabled:
            return False
        
        # Check global tool settings
        tool_setting = ToolSetting.query.filter_by(tool_name=tool_name).first()
        if tool_setting and tool_setting.is_disabled:
            return False
        
        # Check if tool requires paid subscription
        if tool_setting and tool_setting.requires_paid_plan:
            if self.subscription_type == 'free':
                return False
        
        # Check daily usage limits for free users
        if self.subscription_type == 'free':
            today = datetime.utcnow().date()
            if self.last_usage_date != today:
                self.daily_usage_count = 0
                self.last_usage_date = today
                db.session.commit()
            
            daily_limit = ToolSetting.query.filter_by(tool_name='daily_limit').first()
            limit = daily_limit.setting_value if daily_limit else 3
            
            if self.daily_usage_count >= int(limit):
                return False
        
        return True
    
    # Add avatar property for display
    @property
    def avatar_url(self):
        return f"https://ui-avatars.com/api/?name={self.first_name}+{self.last_name}&background=007bff&color=fff"
    
    # Add user avatar class property
    @property
    def user_avatar(self):
        return f"user-avatar d-flex align-items-center justify-content-center rounded-circle bg-primary text-white fw-bold"
    
    def increment_usage(self):
        """Increment daily usage count"""
        today = datetime.utcnow().date()
        if self.last_usage_date != today:
            self.daily_usage_count = 0
            self.last_usage_date = today
        
        self.daily_usage_count += 1
        db.session.commit()
    
    def is_subscription_active(self):
        """Check if user has active subscription"""
        if self.subscription_type == 'free':
            return True
        
        if self.subscription_end and self.subscription_end > datetime.utcnow():
            return True
        
        return False

class ToolUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tool_name = db.Column(db.String(50), nullable=False)
    input_data = db.Column(db.Text)
    output_data = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)

class ActionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class AdminMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ToolSetting class is already defined above

class UserToolRestriction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tool_name = db.Column(db.String(50), nullable=False)
    is_disabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'tool_name', name='unique_user_tool_restriction'),)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_responded = db.Column(db.Boolean, default=False)
    responded_at = db.Column(db.DateTime, nullable=True)
    responded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

class TrademarkSearchCache(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    search_term = db.Column(db.String(200), nullable=False, index=True)
    search_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)  # MD5 hash of search term
    results_data = db.Column(db.Text, nullable=False)  # JSON string of results
    total_results = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    
    @staticmethod
    def get_search_hash(search_term):
        """Generate MD5 hash for search term"""
        import hashlib
        return hashlib.md5(search_term.lower().strip().encode()).hexdigest()
    
    @staticmethod
    def get_cached_results(search_term):
        """Get cached results for a search term if not expired"""
        search_hash = TrademarkSearchCache.get_search_hash(search_term)
        cache = TrademarkSearchCache.query.filter_by(search_hash=search_hash).filter(
            TrademarkSearchCache.expires_at > datetime.utcnow()
        ).first()
        
        if cache:
            import json
            return json.loads(cache.results_data)
        return None
    
    @staticmethod
    def store_results(search_term, results, expiry_hours=24):
        """Store search results in cache"""
        import json
        from datetime import timedelta
        
        search_hash = TrademarkSearchCache.get_search_hash(search_term)
        
        # Remove existing cache for this search term
        TrademarkSearchCache.query.filter_by(search_hash=search_hash).delete()
        
        # Create new cache entry
        cache = TrademarkSearchCache(
            search_term=search_term,
            search_hash=search_hash,
            results_data=json.dumps(results),
            total_results=len(results),
            expires_at=datetime.utcnow() + timedelta(hours=expiry_hours)
        )
        
        db.session.add(cache)
        db.session.commit()
        return cache
    
    @staticmethod
    def cleanup_expired():
        """Remove expired cache entries"""
        TrademarkSearchCache.query.filter(
            TrademarkSearchCache.expires_at <= datetime.utcnow()
        ).delete()
        db.session.commit()


class KdpCategory(db.Model):
    __tablename__ = 'kdp_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    category_path = db.Column(db.Text, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<KdpCategory {self.name}>'
    
    def to_dict(self):
        return {
            'name': self.name,
            'path': self.category_path
        }
    
    @staticmethod
    def search_categories(search_term, limit=50):
        """Search categories by name or path"""
        if not search_term:
            return []
        
        search_term = search_term.lower().strip()
        
        # Search in both name and category_path fields
        query = KdpCategory.query.filter(
            db.or_(
                KdpCategory.name.ilike(f'%{search_term}%'),
                KdpCategory.category_path.ilike(f'%{search_term}%')
            )
        ).order_by(KdpCategory.name)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()

class LoginHistory(db.Model):
    __tablename__ = 'login_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    location = db.Column(db.String(100))
    is_successful = db.Column(db.Boolean, default=True)
    logout_time = db.Column(db.DateTime)
    session_duration = db.Column(db.Integer)  # in minutes
    
    def __repr__(self):
        return f'<LoginHistory {self.user_id} at {self.login_time}>'

class UserSession(db.Model):
    __tablename__ = 'user_session'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_token = db.Column(db.String(64), unique=True, nullable=False)
    device_info = db.Column(db.String(200))
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<UserSession {self.user_id}>'

# Dynamic Website Control Models
class SiteSettings(db.Model):
    """Dynamic website configuration"""
    __tablename__ = 'site_settings'
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text)
    setting_type = db.Column(db.String(20), default='text')  # text, number, boolean, json
    category = db.Column(db.String(50), nullable=False)  # general, tools, prompts, limits
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_setting(key, default_value=None):
        """Get a setting value by key"""
        setting = SiteSettings.query.filter_by(setting_key=key, is_active=True).first()
        if setting:
            if setting.setting_type == 'boolean':
                return setting.setting_value.lower() in ['true', '1', 'yes']
            elif setting.setting_type == 'number':
                try:
                    return int(setting.setting_value)
                except ValueError:
                    return float(setting.setting_value)
            elif setting.setting_type == 'json':
                import json
                return json.loads(setting.setting_value)
            return setting.setting_value
        return default_value
    
    @staticmethod
    def set_setting(key, value, setting_type='text', category='general', description='', user_id=None):
        """Set a setting value"""
        setting = SiteSettings.query.filter_by(setting_key=key).first()
        if setting:
            setting.setting_value = str(value)
            setting.setting_type = setting_type
            setting.category = category
            setting.description = description
            setting.updated_by = user_id
            setting.updated_at = datetime.utcnow()
        else:
            setting = SiteSettings(
                setting_key=key,
                setting_value=str(value),
                setting_type=setting_type,
                category=category,
                description=description,
                updated_by=user_id
            )
            db.session.add(setting)
        db.session.commit()
        return setting

class ToolPrompts(db.Model):
    """Dynamic tool prompts configuration"""
    __tablename__ = 'tool_prompts'
    id = db.Column(db.Integer, primary_key=True)
    tool_name = db.Column(db.String(50), nullable=False)
    prompt_type = db.Column(db.String(30), nullable=False)  # system, user, generation
    prompt_text = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10), default='en')
    is_active = db.Column(db.Boolean, default=True)
    version = db.Column(db.Integer, default=1)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_prompt(tool_name, prompt_type, language='en'):
        """Get active prompt for a tool"""
        prompt = ToolPrompts.query.filter_by(
            tool_name=tool_name,
            prompt_type=prompt_type,
            language=language,
            is_active=True
        ).first()
        return prompt.prompt_text if prompt else None

class UserManagement(db.Model):
    """Extended user management and restrictions"""
    __tablename__ = 'user_management'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    restriction_type = db.Column(db.String(30), nullable=False)  # tool_disabled, daily_limit, feature_locked
    restriction_value = db.Column(db.String(100))  # tool name, limit number, feature name
    reason = db.Column(db.Text)
    applied_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

class SystemActivity(db.Model):
    """Comprehensive system activity monitoring"""
    __tablename__ = 'system_activity'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    activity_type = db.Column(db.String(50), nullable=False)  # login, tool_usage, subscription, admin_action
    activity_details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    severity = db.Column(db.String(10), default='info')  # info, warning, error, critical

class AdminActions(db.Model):
    """Admin action logging for audit trail"""
    __tablename__ = 'admin_actions'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action_type = db.Column(db.String(50), nullable=False)
    action_details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class WebsiteConfiguration(db.Model):
    """Website configuration and settings"""
    __tablename__ = 'website_configuration'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic Site Info
    site_name = db.Column(db.String(100), default='KDP Tools Hub')
    description = db.Column(db.Text, default='Professional KDP Tools Platform')
    contact_email = db.Column(db.String(100), default='support@kdptools.com')
    
    # Visual Settings
    primary_color = db.Column(db.String(7), default='#667eea')
    secondary_color = db.Column(db.String(7), default='#764ba2')
    logo_url = db.Column(db.String(255))
    favicon_url = db.Column(db.String(255))
    
    # Usage Limits
    free_daily_limit = db.Column(db.Integer, default=3)
    premium_daily_limit = db.Column(db.Integer, default=999)
    
    # Feature Toggles
    enable_user_registration = db.Column(db.Boolean, default=True)
    enable_google_auth = db.Column(db.Boolean, default=True)
    enable_login = db.Column(db.Boolean, default=True)
    enable_maintenance = db.Column(db.Boolean, default=False)
    
    # Content Settings
    hero_title = db.Column(db.String(200))
    hero_subtitle = db.Column(db.Text)
    hero_free_text = db.Column(db.String(100))
    hero_no_card_text = db.Column(db.String(100))
    
    # SEO & Analytics
    keywords = db.Column(db.Text)
    google_analytics_id = db.Column(db.String(50))
    google_tag_manager_id = db.Column(db.String(50))
    facebook_pixel_id = db.Column(db.String(50))
    custom_head_tags = db.Column(db.Text)
    
    # Maintenance Settings
    maintenance_title = db.Column(db.String(200), default='Site Under Maintenance')
    maintenance_message = db.Column(db.Text, default='We are currently performing scheduled maintenance. Please check back soon.')
    maintenance_estimated_time = db.Column(db.String(100))
    maintenance_contact_info = db.Column(db.Text)
    
    # Metadata
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    @staticmethod
    def get_config():
        """Get the current website configuration"""
        config = WebsiteConfiguration.query.first()
        if not config:
            # Create default configuration
            config = WebsiteConfiguration()
            db.session.add(config)
            db.session.commit()
        return config
    
    @staticmethod
    def is_maintenance_mode():
        """Check if maintenance mode is enabled"""
        config = WebsiteConfiguration.get_config()
        return config.enable_maintenance
    
    def to_dict(self):
        """Convert configuration to dictionary"""
        return {
            'site_name': self.site_name,
            'description': self.description,
            'contact_email': self.contact_email,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'logo_url': self.logo_url,
            'favicon_url': self.favicon_url,
            'free_daily_limit': self.free_daily_limit,
            'premium_daily_limit': self.premium_daily_limit,
            'enable_user_registration': self.enable_user_registration,
            'enable_google_auth': self.enable_google_auth,
            'enable_login': self.enable_login,
            'enable_maintenance': self.enable_maintenance,
            'hero_title': self.hero_title,
            'hero_subtitle': self.hero_subtitle,
            'hero_free_text': self.hero_free_text,
            'hero_no_card_text': self.hero_no_card_text,
            'keywords': self.keywords,
            'google_analytics_id': self.google_analytics_id,
            'google_tag_manager_id': self.google_tag_manager_id,
            'facebook_pixel_id': self.facebook_pixel_id,
            'custom_head_tags': self.custom_head_tags,
            'maintenance_title': self.maintenance_title,
            'maintenance_message': self.maintenance_message,
            'maintenance_estimated_time': self.maintenance_estimated_time,
            'maintenance_contact_info': self.maintenance_contact_info
        }

class DynamicContent(db.Model):
    """Dynamic website content management"""
    __tablename__ = 'dynamic_content'
    id = db.Column(db.Integer, primary_key=True)
    content_key = db.Column(db.String(100), unique=True, nullable=False)
    content_value = db.Column(db.Text)
    content_type = db.Column(db.String(20), default='html')  # html, text, markdown, json
    page_location = db.Column(db.String(100))  # header, footer, dashboard, tools
    language = db.Column(db.String(10), default='en')
    is_active = db.Column(db.Boolean, default=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_content(key, language='en', default_value=''):
        """Get dynamic content by key"""
        content = DynamicContent.query.filter_by(
            content_key=key,
            language=language,
            is_active=True
        ).first()
        return content.content_value if content else default_value


class SiteConfiguration(db.Model):
    """Website configuration and content management"""
    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    config_value = db.Column(db.Text)
    data_type = db.Column(db.String(20), default='string')  # string, boolean, json, integer
    description = db.Column(db.Text)
    category = db.Column(db.String(50), default='general')  # general, theme, seo, social, security
    is_public = db.Column(db.Boolean, default=False)  # If true, can be accessed without admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __init__(self, config_key, config_value, data_type='string', description=None, category='general', is_public=False):
        self.config_key = config_key
        self.config_value = config_value
        self.data_type = data_type
        self.description = description
        self.category = category
        self.is_public = is_public
    
    @staticmethod
    def get_config(key, default=None):
        """Get configuration value by key"""
        config = SiteConfiguration.query.filter_by(config_key=key).first()
        if not config:
            return default
        
        # Convert based on data type
        if config.data_type == 'boolean':
            return config.config_value.lower() == 'true'
        elif config.data_type == 'integer':
            try:
                return int(config.config_value)
            except (ValueError, TypeError):
                return default
        elif config.data_type == 'json':
            try:
                import json
                return json.loads(config.config_value)
            except (ValueError, TypeError):
                return default
        else:
            return config.config_value
    
    @staticmethod
    def set_config(key, value, data_type='string', description=None, category='general', user_id=None):
        """Set configuration value"""
        config = SiteConfiguration.query.filter_by(config_key=key).first()
        
        # Convert value to string based on type
        if data_type == 'boolean':
            str_value = 'true' if value else 'false'
        elif data_type == 'json':
            import json
            str_value = json.dumps(value)
        else:
            str_value = str(value)
        
        if config:
            config.config_value = str_value
            config.data_type = data_type
            config.updated_at = datetime.utcnow()
            config.updated_by = user_id
            if description:
                config.description = description
        else:
            config = SiteConfiguration(
                config_key=key,
                config_value=str_value,
                data_type=data_type,
                description=description,
                category=category
            )
            config.updated_by = user_id
            db.session.add(config)
        
        db.session.commit()
        return config
    
    @staticmethod
    def get_category_configs(category):
        """Get all configurations for a category"""
        configs = SiteConfiguration.query.filter_by(category=category).all()
        return {config.config_key: config.get_typed_value() for config in configs}
    
    @staticmethod
    def get_public_configs():
        """Get all public configurations (can be accessed without admin)"""
        configs = SiteConfiguration.query.filter_by(is_public=True).all()
        return {config.config_key: config.get_typed_value() for config in configs}
    
    def get_typed_value(self):
        """Get value with proper type conversion"""
        if self.data_type == 'boolean':
            return self.config_value.lower() == 'true'
        elif self.data_type == 'integer':
            try:
                return int(self.config_value)
            except (ValueError, TypeError):
                return 0
        elif self.data_type == 'json':
            try:
                import json
                return json.loads(self.config_value)
            except (ValueError, TypeError):
                return {}
        else:
            return self.config_value


# ToolConfiguration class is already defined above


# MaintenanceMode class is already defined above
    
    @staticmethod
    def toggle_maintenance(enabled, user_id, **kwargs):
        """Toggle maintenance mode"""
        maintenance = MaintenanceMode.query.first()
        if not maintenance:
            maintenance = MaintenanceMode()
            db.session.add(maintenance)
        
        maintenance.is_enabled = enabled
        maintenance.updated_by = user_id
        maintenance.updated_at = datetime.utcnow()
        
        # Update optional fields
        for key, value in kwargs.items():
            if hasattr(maintenance, key):
                setattr(maintenance, key, value)
        
        db.session.commit()
        return maintenance


# Duplicate ToolConfiguration definition removed


