from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from forms import (TitleGeneratorForm, SubtitleGeneratorForm,
                   DescriptionGeneratorForm, AuthorGeneratorForm,
                   KeywordResearchForm, CategoryFinderForm,
                   RoyaltyCalculatorForm, TrademarkSearchForm,
                   ContactForm)
from models import User, ToolUsage, ContactMessage, AdminMessage, KdpCategory, TrademarkSearchCache, ActionLog, LoginHistory, UserSession, ToolSetting
from models import db
from utils import log_action, generate_titles, generate_subtitles, generate_descriptions, generate_author_names, research_keywords, find_categories, calculate_royalty, search_trademarks, sort_trademark_results
# from config_loader import ConfigLoader  # Removed - not needed
from datetime import datetime, timedelta
import json
import hashlib
import secrets

tools_bp = Blueprint('tools', __name__)

def validate_user_session():
    """Validate user session for security"""
    if not current_user.is_authenticated:
        return False
        
    # Check if session token exists and is valid
    if current_user.session_token and current_user.session_expires:
        if datetime.utcnow() > current_user.session_expires:
            current_user.session_token = None
            current_user.session_expires = None
            db.session.commit()
            return False
    
    return True

def check_maintenance_mode():
    """Check if maintenance mode is enabled"""
    maintenance_setting = ToolSetting.query.filter_by(tool_name='maintenance_mode').first()
    return maintenance_setting.setting_value == 'true' if maintenance_setting else False



# =====================================
# MAIN DASHBOARD ROUTE
# =====================================

@tools_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard for users"""
    if not validate_user_session():
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Check maintenance mode
    if check_maintenance_mode() and not current_user.is_admin:
        flash('System is under maintenance. Please try again later.', 'warning')
        return render_template('maintenance.html')
    

    
    # Get available tools using Tools Manager
    from tools_manager import ToolsManager
    available_tools = ToolsManager.get_tools_with_status(current_user)
    
    # Get user stats
    total_usage = ToolUsage.query.filter_by(user_id=current_user.id).count()
    today_usage = ToolUsage.query.filter(
        ToolUsage.user_id == current_user.id,
        ToolUsage.timestamp >= datetime.utcnow().date()
    ).count()
    
    # Get recent activities
    recent_activities = ToolUsage.query.filter_by(user_id=current_user.id).order_by(
        ToolUsage.timestamp.desc()).limit(5).all()
    
    # Get messages
    unread_messages = AdminMessage.query.filter_by(
        user_id=current_user.id, is_read=False).count()
    
    return render_template('tools/dashboard.html',
                         available_tools=available_tools,
                         total_usage=total_usage,
                         today_usage=today_usage,
                         recent_activities=recent_activities,
                         unread_messages=unread_messages)

# =====================================
# TOOL ROUTES - All 8 KDP Tools
# =====================================

@tools_bp.route('/title-generator', methods=['GET', 'POST'])
@login_required
def title_generator():
    """Title Generator Tool"""
    from tools_manager import require_tool_access
    
    # Check tool availability
    from tools_manager import ToolsManager
    availability = ToolsManager.is_tool_available('title_generator')
    if not availability['available']:
        flash(f"Title Generator: {availability['reason']}", 'warning')
        return redirect(url_for('tools.dashboard'))
    
    if not validate_user_session():
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))
    
    if not current_user.email_verified:
        flash('Please verify your email to access tools.', 'warning')
        return redirect(url_for('tools.dashboard'))
    
    form = TitleGeneratorForm()
    generated_titles = []
    
    if form.validate_on_submit():
        try:
            # Generate titles
            book_name = form.book_name.data
            book_type = form.book_type.data
            language = form.language.data
            keywords = form.keywords.data if form.keywords.data else ""
            
            generated_titles = generate_titles(book_name, book_type, language, keywords)
            
            # Record tool usage using Tools Manager
            from tools_manager import ToolsManager
            ToolsManager.record_tool_usage('title_generator', current_user, {
                'book_name': book_name,
                'book_type': book_type,
                'language': language,
                'keywords': keywords,
                'results_count': len(generated_titles)
            })
            
            # Log usage (legacy)
            usage = ToolUsage(
                user_id=current_user.id,
                tool_name='title_generator',
                input_data=json.dumps({
                    'book_name': book_name,
                    'book_type': book_type,
                    'language': language,
                    'keywords': keywords
                }),
                output_data=json.dumps(generated_titles),
                ip_address=request.remote_addr,
                user_agent=str(request.user_agent)
            )
            db.session.add(usage)
            
            # Increment usage count
            current_user.increment_usage()
            db.session.commit()
            
            flash('Titles generated successfully!', 'success')
            
        except Exception as e:
            flash(f'Error generating titles: {str(e)}', 'error')
            
    return render_template('tools/title_generator.html', form=form, generated_titles=generated_titles)

@tools_bp.route('/subtitle-generator', methods=['GET', 'POST'])
@login_required
def subtitle_generator():
    """Subtitle Generator Tool"""
    # Check tool availability using Tools Manager
    from tools_manager import ToolsManager
    availability = ToolsManager.is_tool_available('subtitle_generator')
    if not availability['available']:
        flash(f"Subtitle Generator: {availability['reason']}", 'warning')
        return redirect(url_for('tools.dashboard'))
    
    if not validate_user_session():
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))
    
    if not current_user.email_verified:
        flash('Please verify your email to access tools.', 'warning')
        return redirect(url_for('tools.dashboard'))
    
    form = SubtitleGeneratorForm()
    generated_subtitles = []
    
    if form.validate_on_submit():
        try:
            # Generate subtitles
            book_title = form.book_title.data
            book_type = form.book_type.data
            language = form.language.data
            keywords = form.keywords.data if form.keywords.data else ""
            
            generated_subtitles = generate_subtitles(book_title, book_type, language, keywords)
            
            # Record tool usage using Tools Manager
            from tools_manager import ToolsManager
            ToolsManager.record_tool_usage('subtitle_generator', current_user, {
                'book_title': book_title,
                'book_type': book_type,
                'language': language,
                'keywords': keywords,
                'results_count': len(generated_subtitles)
            })
            
            # Log usage (legacy)
            usage = ToolUsage(
                user_id=current_user.id,
                tool_name='subtitle_generator',
                input_data=json.dumps({
                    'book_title': book_title,
                    'book_type': book_type,
                    'language': language,
                    'keywords': keywords
                }),
                output_data=json.dumps(generated_subtitles),
                ip_address=request.remote_addr,
                user_agent=str(request.user_agent)
            )
            db.session.add(usage)
            
            # Increment usage count
            current_user.increment_usage()
            db.session.commit()
            
            flash('Subtitles generated successfully!', 'success')
            
        except Exception as e:
            flash(f'Error generating subtitles: {str(e)}', 'error')
            
    return render_template('tools/subtitle_generator.html', form=form, generated_subtitles=generated_subtitles)

@tools_bp.route('/description-generator', methods=['GET', 'POST'])
@login_required
def description_generator():
    """Description Generator Tool"""
    if not validate_user_session():
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))
    
    if not current_user.email_verified:
        flash('Please verify your email to access tools.', 'warning')
        return redirect(url_for('tools.dashboard'))
    
    form = DescriptionGeneratorForm()
    generated_description = ""
    
    if form.validate_on_submit():
        try:
            # Check if user can use this tool
            if not current_user.can_use_tool('description_generator'):
                flash('You have reached your daily limit or this tool is disabled.', 'warning')
                return render_template('tools/description_generator.html', form=form, generated_description="")
            
            # Generate description
            book_title = form.book_title.data
            language = form.language.data
            keywords = form.keywords.data if form.keywords.data else ""
            binding_type = form.binding_type.data if form.binding_type.data else ""
            interior_type = form.interior_type.data if form.interior_type.data else ""
            page_count = form.page_count.data if form.page_count.data else ""
            trim_size = form.interior_trim_size.data if form.interior_trim_size.data else ""
            description_length = form.description_length.data
            
            generated_description = generate_descriptions(
                book_title, language, keywords, binding_type, 
                interior_type, page_count, trim_size, description_length
            )
            
            # Log usage
            usage = ToolUsage(
                user_id=current_user.id,
                tool_name='description_generator',
                input_data=json.dumps({
                    'book_title': book_title,
                    'language': language,
                    'keywords': keywords,
                    'binding_type': binding_type,
                    'interior_type': interior_type,
                    'page_count': page_count,
                    'trim_size': trim_size,
                    'description_length': description_length
                }),
                output_data=generated_description,
                ip_address=request.remote_addr,
                user_agent=str(request.user_agent)
            )
            db.session.add(usage)
            
            # Increment usage count
            current_user.increment_usage()
            db.session.commit()
            
            flash('Description generated successfully!', 'success')
            
        except Exception as e:
            flash(f'Error generating description: {str(e)}', 'error')
            
    return render_template('tools/description_generator.html', form=form, generated_description=generated_description)

@tools_bp.route('/author-generator', methods=['GET', 'POST'])
@login_required
def author_generator():
    """Author Generator Tool"""
    if not validate_user_session():
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))
    
    if not current_user.email_verified:
        flash('Please verify your email to access tools.', 'warning')
        return redirect(url_for('tools.dashboard'))
    
    form = AuthorGeneratorForm()
    generated_names = []
    
    if form.validate_on_submit():
        try:
            # Check if user can use this tool
            if not current_user.can_use_tool('author_generator'):
                flash('You have reached your daily limit or this tool is disabled.', 'warning')
                return render_template('tools/author_generator.html', form=form, generated_names=[])
            
            # Generate author names
            language = form.language.data
            country = form.country.data if form.country.data else ""
            gender = form.gender.data
            name_components = {
                'prefix': form.prefix.data,
                'first_name': form.first_name.data,
                'middle_name': form.middle_name.data,
                'last_name': form.last_name.data,
                'suffix': form.suffix.data
            }
            
            generated_names = generate_author_names(language, country, gender, name_components)
            
            # Log usage
            usage = ToolUsage(
                user_id=current_user.id,
                tool_name='author_generator',
                input_data=json.dumps({
                    'language': language,
                    'country': country,
                    'gender': gender,
                    'name_components': name_components
                }),
                output_data=json.dumps(generated_names),
                ip_address=request.remote_addr,
                user_agent=str(request.user_agent)
            )
            db.session.add(usage)
            
            # Increment usage count
            current_user.increment_usage()
            db.session.commit()
            
            flash('Author names generated successfully!', 'success')
            
        except Exception as e:
            flash(f'Error generating author names: {str(e)}', 'error')
            
    return render_template('tools/author_generator.html', form=form, generated_names=generated_names)

@tools_bp.route('/keyword-research', methods=['GET', 'POST'])
@login_required
def keyword_research():
    """Keyword Research Tool"""
    if not validate_user_session():
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))
    
    if not current_user.email_verified:
        flash('Please verify your email to access tools.', 'warning')
        return redirect(url_for('tools.dashboard'))
    
    form = KeywordResearchForm()
    keywords_data = []
    
    if form.validate_on_submit():
        try:
            # Check if user can use this tool
            if not current_user.can_use_tool('keyword_research'):
                flash('You have reached your daily limit or this tool is disabled.', 'warning')
                return render_template('tools/keyword_research.html', form=form, keywords_data=[])
            
            # Research keywords
            topic = form.topic.data
            category = form.category.data
            
            keywords_data = research_keywords(topic, category)
            
            # Log usage
            usage = ToolUsage(
                user_id=current_user.id,
                tool_name='keyword_research',
                input_data=json.dumps({
                    'topic': topic,
                    'category': category
                }),
                output_data=json.dumps(keywords_data),
                ip_address=request.remote_addr,
                user_agent=str(request.user_agent)
            )
            db.session.add(usage)
            
            # Increment usage count
            current_user.increment_usage()
            db.session.commit()
            
            flash('Keywords researched successfully!', 'success')
            
        except Exception as e:
            flash(f'Error researching keywords: {str(e)}', 'error')
            
    return render_template('tools/keyword_research.html', form=form, keywords_data=keywords_data)

@tools_bp.route('/category-finder', methods=['GET', 'POST'])
@login_required
def category_finder():
    """Category Finder Tool"""
    if not validate_user_session():
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))
    
    if not current_user.email_verified:
        flash('Please verify your email to access tools.', 'warning')
        return redirect(url_for('tools.dashboard'))
    
    form = CategoryFinderForm()
    categories_data = []
    total_results = 0
    
    if form.validate_on_submit():
        try:
            # Check if user can use this tool
            if not current_user.can_use_tool('category_finder'):
                flash('You have reached your daily limit or this tool is disabled.', 'warning')
                return render_template('tools/category_finder.html', form=form, categories_data=[], total_results=0)
            
            # Find categories
            search_term = form.search_term.data
            page = request.args.get('page', 1, type=int)
            
            categories_data = find_categories(search_term, page)
            total_results = len(categories_data)
            
            # Log usage
            usage = ToolUsage(
                user_id=current_user.id,
                tool_name='category_finder',
                input_data=json.dumps({
                    'search_term': search_term
                }),
                output_data=json.dumps(categories_data),
                ip_address=request.remote_addr,
                user_agent=str(request.user_agent)
            )
            db.session.add(usage)
            
            # Increment usage count
            current_user.increment_usage()
            db.session.commit()
            
            flash('Categories found successfully!', 'success')
            
        except Exception as e:
            flash(f'Error finding categories: {str(e)}', 'error')
            
    return render_template('tools/category_finder.html', form=form, categories_data=categories_data, total_results=total_results)

@tools_bp.route('/royalty-calculator', methods=['GET', 'POST'])
@login_required
def royalty_calculator():
    """Royalty Calculator Tool"""
    if not validate_user_session():
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))
    
    if not current_user.email_verified:
        flash('Please verify your email to access tools.', 'warning')
        return redirect(url_for('tools.dashboard'))
    
    form = RoyaltyCalculatorForm()
    calculation_results = {}
    
    if form.validate_on_submit():
        try:
            # Check if user can use this tool
            if not current_user.can_use_tool('royalty_calculator'):
                flash('You have reached your daily limit or this tool is disabled.', 'warning')
                return render_template('tools/royalty_calculator.html', form=form, calculation_results={})
            
            # Calculate royalties
            book_type = form.book_type.data
            interior_type = form.interior_type.data
            marketplace = form.marketplace.data
            trim_size = form.trim_size.data
            page_count = form.page_count.data
            list_price = form.list_price.data
            
            calculation_results = calculate_royalty(
                book_type, interior_type, marketplace, 
                trim_size, page_count, list_price
            )
            
            # Log usage
            usage = ToolUsage(
                user_id=current_user.id,
                tool_name='royalty_calculator',
                input_data=json.dumps({
                    'book_type': book_type,
                    'interior_type': interior_type,
                    'marketplace': marketplace,
                    'trim_size': trim_size,
                    'page_count': page_count,
                    'list_price': str(list_price)
                }),
                output_data=json.dumps(calculation_results, default=str),
                ip_address=request.remote_addr,
                user_agent=str(request.user_agent)
            )
            db.session.add(usage)
            
            # Increment usage count
            current_user.increment_usage()
            db.session.commit()
            
            flash('Royalties calculated successfully!', 'success')
            
        except Exception as e:
            flash(f'Error calculating royalties: {str(e)}', 'error')
            
    return render_template('tools/royalty_calculator.html', form=form, calculation_results=calculation_results)

@tools_bp.route('/trademark-search', methods=['GET', 'POST'])
@login_required
def trademark_search():
    """Trademark Search Tool"""
    if not validate_user_session():
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))
    
    if not current_user.email_verified:
        flash('Please verify your email to access tools.', 'warning')
        return redirect(url_for('tools.dashboard'))
    
    form = TrademarkSearchForm()
    search_results = []
    total_results = 0
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', 'status')
    
    if form.validate_on_submit():
        try:
            # Check if user can use this tool
            if not current_user.can_use_tool('trademark_search'):
                flash('You have reached your daily limit or this tool is disabled.', 'warning')
                return render_template('tools/trademark_search.html', form=form, search_results=[], total_results=0, page=1)
            
            # Search trademarks
            search_term = form.search_term.data
            
            # Check cache first
            cached_results = TrademarkSearchCache.get_cached_results(search_term)
            if cached_results:
                search_results = cached_results
            else:
                search_results = search_trademarks(search_term)
                # Cache the results
                TrademarkSearchCache.store_results(search_term, search_results)
            
            # Sort results
            search_results = sort_trademark_results(search_results, sort_by)
            total_results = len(search_results)
            
            # Paginate results
            per_page = 20
            start = (page - 1) * per_page
            end = start + per_page
            search_results = search_results[start:end]
            
            # Log usage
            usage = ToolUsage(
                user_id=current_user.id,
                tool_name='trademark_search',
                input_data=json.dumps({
                    'search_term': search_term
                }),
                output_data=json.dumps({'total_results': total_results}),
                ip_address=request.remote_addr,
                user_agent=str(request.user_agent)
            )
            db.session.add(usage)
            
            # Increment usage count
            current_user.increment_usage()
            db.session.commit()
            
            flash('Trademark search completed successfully!', 'success')
            
        except Exception as e:
            flash(f'Error searching trademarks: {str(e)}', 'error')
            
    return render_template('tools/trademark_search.html', 
                         form=form, 
                         search_results=search_results, 
                         total_results=total_results,
                         page=page,
                         sort_by=sort_by)

# =====================================
# API ROUTES FOR AJAX REQUESTS
# =====================================

@tools_bp.route('/api/search-categories', methods=['POST'])
@login_required
def search_categories():
    """API endpoint for searching categories"""
    if not current_user.email_verified:
        return jsonify({'error': 'Email not verified'}), 403

    if not current_user.can_use_tool('category_finder'):
        return jsonify({'error': 'Tool not available or daily limit reached'}), 403

    search_term = request.json.get('search_term', '').strip()
    page = request.json.get('page', 1)
    per_page = 20

    if not search_term:
        return jsonify({'categories': [], 'total_results': 0, 'total_pages': 0, 'current_page': 1})

    # Search in database
    all_categories = KdpCategory.search_categories(search_term, limit=None)
    total_results = len(all_categories)
    
    # Calculate pagination
    total_pages = ((total_results - 1) // per_page) + 1 if total_results > 0 else 0
    start = (page - 1) * per_page
    end = start + per_page
    paginated_categories = all_categories[start:end]

    # Convert to JSON format
    results = []
    for category in paginated_categories:
        results.append({
            'id': category.id,
            'name': category.name,
            'path': category.category_path
        })

    # Log usage (only for new searches, not pagination)
    if page == 1:
        usage = ToolUsage(
            user_id=current_user.id,
            tool_name='category_finder',
            input_data=json.dumps({'search_term': search_term}),
            output_data=json.dumps({'total_results': total_results}),
            ip_address=request.remote_addr,
            user_agent=str(request.user_agent)
        )
        db.session.add(usage)
        current_user.increment_usage()
        db.session.commit()

    return jsonify({
        'categories': results,
        'total_results': total_results,
        'total_pages': total_pages,
        'current_page': page,
        'per_page': per_page
    })

# =====================================
# SETTINGS AND ACCOUNT MANAGEMENT
# =====================================

@tools_bp.route('/settings')
@login_required
def settings():
    """User settings page"""
    if not validate_user_session():
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))
    
    return render_template('tools/settings.html')

@tools_bp.route('/messages')
@login_required
def messages():
    """User messages page"""
    if not validate_user_session():
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))
    
    user_messages = AdminMessage.query.filter_by(
        user_id=current_user.id).order_by(
            AdminMessage.created_at.desc()).all()

    # Mark all messages as read
    for message in user_messages:
        message.is_read = True
    db.session.commit()

    return render_template('tools/messages.html', messages=user_messages)

@tools_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form"""
    form = ContactForm()

    if form.validate_on_submit():
        message = ContactMessage(
            name=form.name.data,
            email=form.email.data,
            subject=form.subject.data,
            message=form.message.data
        )
        db.session.add(message)
        db.session.commit()

        if current_user.is_authenticated:
            log_action(current_user.id, 'contact_message',
                       f'Sent contact message: {form.subject.data}',
                       request.remote_addr, str(request.user_agent))

        flash('Your message has been sent successfully! We will get back to you soon.', 'success')
        return redirect(url_for('tools.contact'))

    return render_template('contact.html', form=form)

# =====================================
# ACCOUNT MANAGEMENT API ROUTES
# =====================================

@tools_bp.route('/save-account-settings', methods=['POST'])
@login_required
def save_account_settings():
    """Save account settings"""
    try:
        data = request.get_json()
        
        # Update user information
        current_user.first_name = data.get('first_name', current_user.first_name)
        current_user.last_name = data.get('last_name', current_user.last_name)
        
        db.session.commit()
        
        log_action(current_user.id, 'account_settings_updated', 
                   'Updated account information',
                   request.remote_addr, str(request.user_agent))
        
        return jsonify({'success': True, 'message': 'Account settings saved successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@tools_bp.route('/change-email', methods=['POST'])
@login_required
def change_email():
    """Change user email"""
    try:
        data = request.get_json()
        new_email = data.get('new_email')
        current_password = data.get('current_password')
        
        # Verify current password
        if not current_user.check_password(current_password):
            return jsonify({'success': False, 'message': 'Current password is incorrect'})
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=new_email).first()
        if existing_user:
            return jsonify({'success': False, 'message': 'Email already exists'})
        
        # Update email
        current_user.email = new_email
        current_user.email_verified = False  # Require re-verification
        
        db.session.commit()
        
        log_action(current_user.id, 'email_changed', 
                   f'Changed email to {new_email}',
                   request.remote_addr, str(request.user_agent))
        
        return jsonify({'success': True, 'message': 'Email changed successfully. Please verify your new email.'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@tools_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        # Verify current password
        if not current_user.check_password(current_password):
            return jsonify({'success': False, 'message': 'Current password is incorrect'})
        
        # Validate new password
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters long'})
        
        # Update password
        current_user.set_password(new_password)
        
        db.session.commit()
        
        log_action(current_user.id, 'password_changed', 
                   'Changed password',
                   request.remote_addr, str(request.user_agent))
        
        return jsonify({'success': True, 'message': 'Password changed successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@tools_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account"""
    try:
        data = request.get_json()
        confirmation = data.get('confirmation')
        password = data.get('password')
        
        # Verify confirmation text
        if confirmation != 'DELETE':
            return jsonify({'success': False, 'message': 'Please type DELETE to confirm'})
        
        # Verify password
        if not current_user.check_password(password):
            return jsonify({'success': False, 'message': 'Password is incorrect'})
        
        # Log action before deletion
        log_action(current_user.id, 'account_deleted', 
                   'Account deleted by user',
                   request.remote_addr, str(request.user_agent))
        
        # Delete user account
        db.session.delete(current_user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Account deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})