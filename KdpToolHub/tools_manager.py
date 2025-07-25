#!/usr/bin/env python3
"""
Tools Manager - System to manage tool availability and access control
"""

from flask import current_app, session, flash, redirect, url_for
from flask_login import current_user
from models import ToolConfiguration, ToolUsage, User, db
from datetime import datetime, timedelta
from functools import wraps

class ToolsManager:
    """Centralized tools management system"""
    
    @staticmethod
    def is_tool_available(tool_name, user=None):
        """
        Check if a tool is available for the current user
        
        Args:
            tool_name (str): Name of the tool to check
            user (User): User object (optional, uses current_user if not provided)
            
        Returns:
            dict: {
                'available': bool,
                'reason': str,
                'tool_config': ToolConfiguration
            }
        """
        if user is None:
            try:
                user = current_user if current_user and current_user.is_authenticated else None
            except:
                user = None
        
        # Get tool configuration
        tool_config = ToolConfiguration.get_tool_by_name(tool_name)
        
        if not tool_config:
            return {
                'available': False,
                'reason': 'Tool not found',
                'tool_config': None
            }
        
        # Check if tool is enabled
        if not tool_config.is_enabled:
            return {
                'available': False,
                'reason': 'Tool is currently disabled',
                'tool_config': tool_config
            }
        
        # Check if user is authenticated for premium tools
        if tool_config.requires_paid_plan:
            if not user or not user.is_authenticated:
                return {
                    'available': False,
                    'reason': 'Please login to access this premium tool',
                    'tool_config': tool_config
                }
            
            # Check subscription status
            if user.subscription_type not in ['monthly', 'yearly']:
                return {
                    'available': False,
                    'reason': 'This tool requires a premium subscription',
                    'tool_config': tool_config
                }
        
        # Check daily usage limits
        if user and user.is_authenticated:
            daily_limit = tool_config.premium_daily_limit if user.subscription_type in ['monthly', 'yearly'] else tool_config.free_daily_limit
            
            # Count today's usage
            today = datetime.utcnow().date()
            today_usage = ToolUsage.query.filter(
                ToolUsage.user_id == user.id,
                ToolUsage.tool_name == tool_name,
                db.func.date(ToolUsage.timestamp) == today
            ).count()
            
            if today_usage >= daily_limit:
                return {
                    'available': False,
                    'reason': f'Daily limit reached ({daily_limit} uses per day)',
                    'tool_config': tool_config
                }
        
        return {
            'available': True,
            'reason': 'Tool is available',
            'tool_config': tool_config
        }
    
    @staticmethod
    def get_available_tools(user=None):
        """
        Get list of all available tools for a user
        
        Args:
            user (User): User object (optional)
            
        Returns:
            list: List of available tool configurations
        """
        if user is None:
            try:
                user = current_user if current_user and current_user.is_authenticated else None
            except:
                user = None
        
        all_tools = ToolConfiguration.get_enabled_tools()
        available_tools = []
        
        for tool in all_tools:
            availability = ToolsManager.is_tool_available(tool.tool_name, user)
            if availability['available']:
                available_tools.append(tool)
        
        return available_tools
    
    @staticmethod
    def get_tools_with_status(user=None):
        """
        Get all tools with their availability status
        
        Args:
            user (User): User object (optional)
            
        Returns:
            list: List of tools with status information
        """
        if user is None:
            try:
                user = current_user if current_user and current_user.is_authenticated else None
            except:
                user = None
        
        all_tools = ToolConfiguration.query.order_by(ToolConfiguration.sort_order).all()
        tools_with_status = []
        
        for tool in all_tools:
            availability = ToolsManager.is_tool_available(tool.tool_name, user)
            
            # Get usage statistics
            usage_stats = ToolsManager.get_tool_usage_stats(tool.tool_name, user)
            
            tool_info = {
                'config': tool,
                'available': availability['available'],
                'reason': availability['reason'],
                'usage_stats': usage_stats
            }
            
            tools_with_status.append(tool_info)
        
        return tools_with_status
    
    @staticmethod
    def get_tool_usage_stats(tool_name, user=None):
        """
        Get usage statistics for a tool
        
        Args:
            tool_name (str): Name of the tool
            user (User): User object (optional)
            
        Returns:
            dict: Usage statistics
        """
        if user is None:
            try:
                user = current_user if current_user and current_user.is_authenticated else None
            except:
                user = None
        
        stats = {
            'total_uses': 0,
            'today_uses': 0,
            'remaining_today': 0,
            'daily_limit': 0
        }
        
        if user and user.is_authenticated:
            tool_config = ToolConfiguration.get_tool_by_name(tool_name)
            if tool_config:
                # Get daily limit
                stats['daily_limit'] = tool_config.premium_daily_limit if user.subscription_type in ['monthly', 'yearly'] else tool_config.free_daily_limit
                
                # Count total uses
                stats['total_uses'] = ToolUsage.query.filter(
                    ToolUsage.user_id == user.id,
                    ToolUsage.tool_name == tool_name
                ).count()
                
                # Count today's uses
                today = datetime.utcnow().date()
                stats['today_uses'] = ToolUsage.query.filter(
                    ToolUsage.user_id == user.id,
                    ToolUsage.tool_name == tool_name,
                    db.func.date(ToolUsage.timestamp) == today
                ).count()
                
                # Calculate remaining uses
                stats['remaining_today'] = max(0, stats['daily_limit'] - stats['today_uses'])
        
        return stats
    
    @staticmethod
    def record_tool_usage(tool_name, user=None, additional_data=None):
        """
        Record tool usage in the database
        
        Args:
            tool_name (str): Name of the tool used
            user (User): User object (optional)
            additional_data (dict): Additional data to store
            
        Returns:
            bool: Success status
        """
        try:
            if user is None:
                user = current_user if current_user.is_authenticated else None
            
            usage = ToolUsage(
                user_id=user.id if user else None,
                tool_name=tool_name,
                timestamp=datetime.utcnow(),
                additional_data=additional_data
            )
            
            db.session.add(usage)
            db.session.commit()
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error recording tool usage: {e}")
            db.session.rollback()
            return False

def require_tool_access(tool_name):
    """
    Decorator to check tool access before allowing function execution
    
    Args:
        tool_name (str): Name of the tool to check
        
    Returns:
        decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check tool availability
            availability = ToolsManager.is_tool_available(tool_name)
            
            if not availability['available']:
                # Handle different reasons
                if 'disabled' in availability['reason'].lower():
                    flash('This tool is currently under maintenance. Please try again later.', 'warning')
                elif 'premium' in availability['reason'].lower():
                    flash('This tool requires a premium subscription. Please upgrade your account.', 'info')
                elif 'login' in availability['reason'].lower():
                    flash('Please login to access this tool.', 'info')
                    return redirect(url_for('auth.login'))
                elif 'limit' in availability['reason'].lower():
                    flash(f'Daily usage limit reached. {availability["reason"]}', 'warning')
                else:
                    flash(f'Tool not available: {availability["reason"]}', 'error')
                
                # Redirect to appropriate page
                if current_user.is_authenticated:
                    return redirect(url_for('main.dashboard'))
                else:
                    return redirect(url_for('main.index'))
            
            # Record tool usage
            ToolsManager.record_tool_usage(tool_name)
            
            # Execute the original function
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def get_tools_for_navigation():
    """
    Get tools for navigation menu with proper filtering
    
    Returns:
        list: List of available tools for navigation
    """
    return ToolsManager.get_available_tools()

def get_tool_card_data(tool_name):
    """
    Get tool card data for display
    
    Args:
        tool_name (str): Name of the tool
        
    Returns:
        dict: Tool card data
    """
    availability = ToolsManager.is_tool_available(tool_name)
    usage_stats = ToolsManager.get_tool_usage_stats(tool_name)
    
    return {
        'config': availability['tool_config'],
        'available': availability['available'],
        'reason': availability['reason'],
        'usage_stats': usage_stats
    }