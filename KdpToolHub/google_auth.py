# Use this Flask blueprint for Google authentication. Do not use flask-dance.

import json
import os

import requests
from models import db
from flask import Blueprint, redirect, request, url_for, flash
from flask_login import login_required, login_user, logout_user
from models import User
from oauthlib.oauth2 import WebApplicationClient
from utils import log_action
# from config_loader import ConfigLoader  # Removed - not needed

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "your-google-client-id")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "your-google-client-secret")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Make sure to use this redirect URL. It has to match the one in the whitelist
DEV_REDIRECT_URL = f'https://{os.environ.get("REPLIT_DEV_DOMAIN", "localhost:5000")}/google_login/callback'

# ALWAYS display setup instructions to the user:
print(f"""To make Google authentication work:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new OAuth 2.0 Client ID
3. Add {DEV_REDIRECT_URL} to Authorized redirect URIs

For detailed instructions, see:
https://docs.replit.com/additional-resources/google-auth-in-flask#set-up-your-oauth-app--client
""")

client = WebApplicationClient(GOOGLE_CLIENT_ID)

google_auth = Blueprint("google_auth", __name__)


@google_auth.route("/google_login")
def login():
    # Check if Google authentication is enabled
    if not ConfigLoader.is_google_auth_enabled():
        flash('Google authentication is currently disabled. Please use email/password login.', 'error')
        return redirect(url_for('auth.login'))
    
    # Check if user registration is enabled for new Google users
    if not ConfigLoader.is_user_registration_enabled():
        flash('User registration is currently disabled. Please contact support.', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        # Use the exact redirect URI that should be whitelisted in Google Console
        redirect_uri = DEV_REDIRECT_URL
        
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=redirect_uri,
            scope=["openid", "email", "profile"],
        )
        return redirect(request_uri)
    except Exception as e:
        flash(f'Google authentication error: {str(e)}', 'error')
        return redirect(url_for('auth.login'))


@google_auth.route("/google_login/callback")
def callback():
    try:
        code = request.args.get("code")
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]

        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url.replace("http://", "https://"),
            redirect_url=DEV_REDIRECT_URL,
            code=code,
        )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )

        client.parse_request_body_response(json.dumps(token_response.json()))

        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        userinfo = userinfo_response.json()
        if userinfo.get("email_verified"):
            users_email = userinfo["email"]
            users_name = userinfo.get("given_name", userinfo.get("name", "User"))
            users_family_name = userinfo.get("family_name", "")
        else:
            flash("User email not available or not verified by Google.", 'error')
            return redirect(url_for('auth.login'))

        user = User.query.filter_by(email=users_email).first()
        if not user:
            # Create new user from Google data
            user = User(
                username=users_email.split('@')[0],  # Use email prefix as username
                email=users_email,
                first_name=users_name,
                last_name=users_family_name,
                email_verified=True,  # Google email is already verified
                country='',  # Will be filled later
                city='',
                address=''
            )
            db.session.add(user)
            db.session.commit()
            
            log_action(user.id, 'google_register', 'User registered via Google', 
                      request.remote_addr, request.user_agent.string)
            flash('Welcome! Please complete your profile in account settings.', 'info')
        else:
            log_action(user.id, 'google_login', 'User logged in via Google', 
                      request.remote_addr, request.user_agent.string)

        login_user(user)
        return redirect(url_for("tools.dashboard"))
        
    except Exception as e:
        flash(f'Google authentication error: {str(e)}', 'error')
        return redirect(url_for('auth.login'))


@google_auth.route("/logout")
@login_required
def logout():
    from flask_login import current_user
    from utils import log_action
    log_action(current_user.id, 'logout', 'User logged out', 
              request.remote_addr, request.user_agent.string)
    logout_user()
    return redirect(url_for("index"))
