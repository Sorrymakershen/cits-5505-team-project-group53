from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Create the Flask application
app = Flask(__name__)

# Configure the application
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-temporary-key')  # Use environment variable in production
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///travel_planner.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = False  # 临时禁用 CSRF 保护以解决问题

# Google Maps API Key
app.config['GOOGLE_MAPS_API_KEY'] = os.environ.get('GOOGLE_MAPS_API_KEY', '')

# Initialize CSRF protection
from app.csrf_config import configure_csrf
csrf = configure_csrf(app)

# initialize the database and migration
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# import models
from app.models import user, travel_plan, memory

def create_app():
    
    # Import user loader function
    from app import auth
    
    # Register custom template filters
    from app.template_filters import register_filters
    register_filters(app)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.planner import planner_bp
    from app.routes.memories import memories_bp
    from app.routes.main import main_bp
    from app.routes.statistics import statistics_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(planner_bp)
    app.register_blueprint(memories_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(statistics_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
