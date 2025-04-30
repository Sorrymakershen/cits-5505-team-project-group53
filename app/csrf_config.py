"""CSRF Protection Configuration Module

This module configures Cross-Site Request Forgery (CSRF) protection for the application.
CSRF is a type of attack where unauthorized commands are submitted from a user that the
web application trusts. The protection works by:

1. Creating a unique token for each user session
2. Requiring this token to be included in all POST/PUT/DELETE requests
3. Validating the token server-side to ensure the request is legitimate

Routes that need to be exempt from CSRF protection (like API endpoints with their own
authentication) can be added to the WTF_CSRF_EXEMPT_LIST.
"""

def configure_csrf(app):
    """Configure CSRF protection for the Flask application
    
    Args:
        app: The Flask application instance
        
    Returns:
        CSRFProtect: The configured CSRF protection instance
    """
    app.config['WTF_CSRF_CHECK_DEFAULT'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour token expiration
    
    # Routes that are exempt from CSRF protection
    # Only add routes here if they:
    # 1. Have their own authentication mechanism (like API tokens)
    # 2. Need to receive requests from external systems that cannot include CSRF tokens
    app.config['WTF_CSRF_EXEMPT_LIST'] = ['/statistics/set-home-location', '/statistics/validate-address']

    # Enable CSRF protection
    from flask_wtf.csrf import CSRFProtect
    csrf = CSRFProtect(app)
    return csrf
