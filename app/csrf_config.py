"""CSRF Protection Configuration Module"""

def configure_csrf(app):
    """Configure CSRF protection for the Flask application"""
    app.config['WTF_CSRF_CHECK_DEFAULT'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour token expiration
    
    # 设置需要排除的路由
    app.config['WTF_CSRF_EXEMPT_LIST'] = ['/statistics/set-home-location', '/statistics/validate-address']

    # Enable CSRF protection
    from flask_wtf.csrf import CSRFProtect
    csrf = CSRFProtect(app)
    return csrf
