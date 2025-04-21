import streamlit as st
from services.auth import GoogleWorkspaceAuth, login
import time

def auth_callback():
    """Handle OAuth callback"""
    auth = GoogleWorkspaceAuth()
    
    # Get authorization code from URL parameters
    code = st.query_params.get("code")
    
    if code:
        try:
            # Get credentials from authorization code
            flow = auth.create_oauth_flow()
            flow.fetch_token(code=code)
            
            # Get user info from credentials
            credentials = flow.credentials
            user_info = auth.verify_oauth_token(credentials.id_token)
            
            if user_info:
                st.session_state['user_info'] = user_info
                st.success("Successfully authenticated!")
                time.sleep(2)
                # Redirect to home page
                st.query_params.clear()
                st.switch_page("app.py")
            else:
                # st.error("Authentication failed: Invalid token or unauthorized domain")
                st.error("failed ahhh")
        except Exception as e:
            st.error(f"Hi!")
    else:
        st.error("Hello!")

if __name__ == "__main__":
    auth_callback()
