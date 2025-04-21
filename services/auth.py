import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
import streamlit as st
from datetime import datetime, timedelta

class GoogleWorkspaceAuth:
    """Google Workspace authentication handler"""
    
    def __init__(self):
        """Initialize the auth handler with configuration from environment variables"""
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        self.redirect_uri = os.getenv('OAUTH_REDIRECT_URI')
        self.allowed_domains = os.getenv('ALLOWED_DOMAINS', '').split(',')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set")
    
    def create_oauth_flow(self):
        """Create and configure Google OAuth flow"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile"
            ]
        )
        flow.redirect_uri = self.redirect_uri
        return flow

    def verify_oauth_token(self, token):
        """Verify the OAuth token and get user info"""
        try:
            idinfo = id_token.verify_oauth2_token(
                token, requests.Request(), self.client_id)

            # Verify domain if restricted
            if self.allowed_domains and self.allowed_domains[0]:  # Check if list is not empty
                email_domain = idinfo['email'].split('@')[1]
                if email_domain not in self.allowed_domains:
                    return None

            return {
                'email': idinfo['email'],
                'name': idinfo.get('name', 'User'),
                'picture': idinfo.get('picture')  # Will be None if not present
            }
        except Exception as e:
            st.error(f"Token verification failed: {e}")
            return None

def init_auth_state():
    """Initialize authentication state"""
    if 'auth_state' not in st.session_state:
        st.session_state.auth_state = {
            'is_authenticated': False,
            'user': None,
            'last_activity': None
        }

def check_auth():
    """Check if user is authenticated and session is valid"""
    init_auth_state()
    
    # Check if authenticated
    if not st.session_state.auth_state['is_authenticated']:
        return False

    # Check session timeout (30 minutes)
    if st.session_state.auth_state['last_activity']:
        timeout = datetime.now() - st.session_state.auth_state['last_activity']
        if timeout > timedelta(minutes=60):
            logout()
            return False

    # Update last activity
    st.session_state.auth_state['last_activity'] = datetime.now()
    return True

def login(user_info):
    """Log in user"""
    st.session_state.auth_state['is_authenticated'] = True
    st.session_state.auth_state['user'] = user_info
    st.session_state.auth_state['last_activity'] = datetime.now()

def logout():
    """Log out user"""
    st.session_state.auth_state = {
        'is_authenticated': False,
        'user': None,
        'last_activity': None
    }
